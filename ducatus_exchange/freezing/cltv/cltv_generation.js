//для начала выполнить npm install импортируемых пакетов:
const bitcoin = require('bitcoinjs-lib');
const bip65 = require('bip65');
const fs = require('fs');

const scriptArgs = process.argv.slice(2);

//алиса - получатель сможет получить деньги, когда пройдет время блокировки
//боб - отправитель. Боб и Алиса могут разблокировать деньги вместе до истечения времени блокировки.
const alicePublic = scriptArgs[0];
const bobPublic = scriptArgs[1];

const lockTime = bip65.encode({utc: Number(scriptArgs[2])});

const savingDir = scriptArgs[3];

const network = bitcoin.networks.bitcoin;
network.public = 0x019da462;
network.private = 0x019d9cfe;
network.pubKeyHash = 0x31;
network.scriptHash = 0x33;
network.wif = 0xb1;

const redeemScript = cltvCheckSigOutput(alicePublic, bobPublic, lockTime);

console.log('redeemScript\n', redeemScript.toString('hex'));

const p2sh = bitcoin.payments.p2sh({redeem: {output: redeemScript, network}, network});

//адрес полученный из скрипта. Можем отправлять на него деньги. А вывести сможем, когда настанет момент locktime
console.log('P2SH address\n', p2sh.address);

saveLockTransactionInfo(redeemScript.toString('hex'), p2sh.address, lockTime, savingDir);


function cltvCheckSigOutput (aQ, bQ, lockTime) {
  return bitcoin.script.compile([
    bitcoin.opcodes.OP_IF,
    bitcoin.script.number.encode(lockTime),
    bitcoin.opcodes.OP_CHECKLOCKTIMEVERIFY,
    bitcoin.opcodes.OP_DROP,

    bitcoin.opcodes.OP_ELSE,
    // bQ.publicKey,
    new Buffer.from(bQ, 'hex'),
    bitcoin.opcodes.OP_CHECKSIGVERIFY,
    bitcoin.opcodes.OP_ENDIF,

    // aQ.publicKey,
    new Buffer.from(aQ, 'hex'),
    bitcoin.opcodes.OP_CHECKSIG
  ])
}

function saveLockTransactionInfo(script, address, voucherId, savingDir) {
    fs.writeFile(`${savingDir}/redeemScript-${lockTime}.txt`, script, function (err) {
        if (err) return console.log(err);
        console.log("redeem script saved");
      });

    fs.writeFile(`${savingDir}/lockAddress-${lockTime}.txt`, address, function (err) {
        if (err) return console.log(err);
        console.log("lock address saved");
    });
}
