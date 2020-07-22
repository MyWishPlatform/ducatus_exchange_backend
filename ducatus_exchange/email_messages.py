lottery_subject = """Hello"""

lottery_text = """Hello, you are new lottery player
Your tx hash {tx_hash}
Your tickets amount {tickets_amount}"""

promo_codes_text = """
Your backoffice code {back_office_code}
Your e-commerce code {e_commerce_code}"""

lottery_html_body = """<!DOCTYPE html
  PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>Ducatus Email</title>
  <style type="text/css">
    body {
      margin: 0;
      padding: 0;
      min-width: 100% !important;
      font-family: sans-serif;
    }

    img {
      height: auto;
    }

    .content {
      width: 100%;
      max-width: 450px;
    }

    .header {
      text-align: center;
      padding: 20px;
    }

    .innerpadding {
      padding: 30px 20px 30px 20px;
    }

    .spacer {
      padding: 10px 20px 10px 20px;
    }

    .subhead {
      font-size: 15px;
      color: #ffffff;
      font-family: sans-serif;
      letter-spacing: 10px;
    }

    .h2 {
      padding: 0 0 15px 0;
      font-size: 14px;
      font-weight: 300;
      line-height: 28px;
      text-align: center;
    }

    .accent {
      padding: 10px 0 30px 0;
      font-size: 18px;
      font-weight: 400;
      color: #892734;
      text-align: center;
    }

    .bodycopy {
      padding: 0 10px 15px 10px;
      font-size: 15px;
      font-weight: 300;
      text-align: center;
      line-height: 18px;
    }

    table {
      border-collapse: separate;
    }

    tr:first-child td:first-child {
      border-top-left-radius: 20px;
    }

    tr:first-child td:last-child {
      border-top-right-radius: 20px;
    }

    tr:last-child td:first-child {
      border-bottom-left-radius: 20px;
    }

    tr:last-child td:last-child {
      border-bottom-right-radius: 20px;
    }

    .bg-lightpink {
      background-color: #eededf;
    }

    .bg-lightgray {
      background-color: #f1f2f4;
    }

    .voucher-title {
      font-size: 16px;
      color: #4c4949;
      font-weight: 500;
      padding: 0px 10px 15px 10px;
    }

    .voucher-text {
      font-size: 15px;
      color: #4c4949;
      font-weight: 300;
      padding: 0px 10px 15px 10px;
    }

    .voucher-link {
      font-size: 15px;
      color: #4c4949;
      font-weight: 300;
    }

    .voucher-code {
      padding: 0px 10px 15px 10px;
      text-transform: uppercase;
    }

    .voucher-text {
      font-size: 15px;
      color: #4c4949;
      font-weight: 300;
      padding: 0px 10px 15px 10px;
    }

    .voucher-info {
      font-size: 13px;
      color: #4c4949;
      font-weight: 300;
      padding: 20px 10px 0px 10px;
    }

    .borderbottom {
      border-bottom: 1px solid black;
    }
  </style>
</head>

<body ducatus bgcolor="#ffffff">
  <table width="100%" bgcolor="#ffffff" border="0" cellpadding="0" cellspacing="0">
    <tr>
      <td>
        <table bgcolor="#ffffff" class="content" align="center" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="border-radius: 0px;" bgcolor="#f1f2f4" class="header">
              <img class="fix" src="https://www.ducatuscoins.com/assets/img/ducatus-logo-first.png" width="150"
                height="150" border="0" alt="" />
            </td>
          </tr>
          <tr>
            <td class="innerpadding">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td class="h2">
                    Your DUC Purchase Confirmation for $X
                  </td>
                </tr>
                <tr>
                  <td class="accent">Thank you for purchasing DUC.</td>
                </tr>
                <tr>
                  <td class="bodycopy">We have received your payment and your hash has been added to our list of
                    elogible entries:</td>
                </tr>
                <tr>
                  <td class="bodycopy" style="padding: 10px 0px 20px 0;">X YOUR HASH NUMBER X</td>
                </tr>
                <tr>
                  <td class="bodycopy">In addition to your X entries to win a limited-edition luxury watch, you have
                    also earned:</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="bg-lightpink innerpadding">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td class="voucher-title">X% extra DSV (Digital Shopping Voucher)</td>
                </tr>
                <tr>
                  <td class="voucher-text">To redeem, purchase any DSV package at our Ducatus Network Member's site <a
                      href="https://network.ducatus.com/" class="voucher-link">https://network.ducatus.com</a></td>
                </tr>
                <tr>
                  <td class="voucher-text">Not a member yet? Register now and earn even more with the Ducatus Cashless
                    Economy.</td>
                </tr>
                <tr>
                  <td class="borderbottom"></td>
                </tr>
                <tr>
                  <td class="voucher-text" style="padding-top: 15px;">Use this Voucher Code* upon checkout to claim your
                    extra DSV:</td>
                </tr>
                <tr>
                  <td class="voucher-code"><i>X YOUR EXTRA DSV VOUCHER CODE X</i></td>
                </tr>
                <tr>
                  <td class="voucher-info">*Valid from now until 15 Aug 2020, one-time purchase only.</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="spacer"></td>
          </tr>
          <tr>
            <td class="bg-lightgray innerpadding">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td class="voucher-title">X% discount for any purchase at D-Shop</td>
                </tr>
                <tr>
                  <td class="voucher-text">To redeem, purchase any DSV item at D-Shop on our eCommerce site Remus Nation
                    <a href="https://remusnation.com/dshop/" class="voucher-link">https://remusnation.com/dshop</a></td>
                </tr>
                <tr>
                  <td class="borderbottom"></td>
                </tr>
                <tr>
                  <td class="voucher-text" style="padding-top: 15px;">Use this Voucher Code* upon checkout to apply your
                    discount:</td>
                </tr>
                <tr>
                  <td class="voucher-code"><i>X YOUR DISCOUNT VOUCHER CODE X</i></td>
                </tr>
                <tr>
                  <td class="voucher-info">*Valid from now until 31 Dec 2020, one-time purchase only.</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="spacer"></td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>

</html>"""
