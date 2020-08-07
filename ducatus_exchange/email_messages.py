lottery_html_style = """<!DOCTYPE html
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
</head>"""

lottery_html_body = """<body ducatus bgcolor="#ffffff">
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
                  <td class="accent">Thank you for purchasing DUC.</td>
                </tr>
                <tr>
                  <td class="bodycopy">We have received your payment and your hash has been added to our list of
                    eligible entries:</td>
                </tr>
                <tr>
                  <td class="bodycopy" style="padding: 10px 0px 20px 0;">{tx_hash}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

lottery_bonuses_html_body = """<body ducatus bgcolor="#ffffff">
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
                  <td class="accent">Thank you for purchasing DUC.</td>
                </tr>
                <tr>
                  <td class="bodycopy">We have received your payment and your hash has been added to our list of
                    eligible entries:</td>
                </tr>
                <tr>
                  <td class="bodycopy" style="padding: 10px 0px 20px 0;">{tx_hash}</td>
                </tr>
                <tr>
                  <td class="bodycopy">In addition to your {tickets_amount} entries to win a limited-edition luxury watch, you have
                    also earned:</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="bg-lightpink innerpadding">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td class="voucher-title">{back_office_bonus}% extra DSV (Digital Shopping Voucher)</td>
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
                  <td class="voucher-code">{back_office_code}</td>
                </tr>
                <tr>
                  <td class="voucher-info">*Valid from now until <b>15 Aug 2020</b>, one-time purchase only.</td>
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
                  <td class="voucher-title">{e_commerce_bonus}% discount for any purchase at D-Shop</td>
                </tr>
                <tr>
                  <td class="voucher-text">To redeem, purchase any item at D-Shop on our eCommerce site Remus Nation
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
                  <td class="voucher-code">{e_commerce_code}</td>
                </tr>
                <tr>
                  <td class="voucher-info">*Valid from now until <b>31 Dec 2020</b>, one-time purchase only.</td>
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

warning_html_style = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Ducatus Second Mail</title>
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

      .accent {
        padding: 10px 0 20px 0;
        font-size: 20px;
        font-weight: 400;
        color: #892734;
        text-align: center;
      }

      .body-text {
        padding: 0px 15px 15px 15px;
        font-size: 15px;
        font-weight: 300;
        text-align: center;
        line-height: 18px;
      }

      .body-link {
        color: black;
      }

      .text-heavy-underline {
        text-transform: uppercase;
        text-decoration: underline;
        color: black;
        font-weight: bold;
      }

      .btn {
        padding: 5px 30px 5px 30px;
        text-transform: uppercase;
        color: black;
        border: 1px solid black;
        border-radius: 20px;
        text-decoration: none;
        font-size: 20px;
        font-weight: 400;
      }

      .ta-c {
        text-align: center;
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
    </style>
  </head>"""

warning_html_body = """<body ducatus bgcolor="#ffffff">
    <table
      width="100%"
      bgcolor="#ffffff"
      border="0"
      cellpadding="0"
      cellspacing="0"
    >
      <tr>
        <td>
          <table
            bgcolor="#ffffff"
            class="content"
            align="center"
            cellpadding="0"
            cellspacing="0"
            border="0"
          >
            <tr>
              <td style="border-radius: 0px;" bgcolor="#f1f2f4" class="header">
                <img
                  class="fix"
                  src="https://www.ducatuscoins.com/assets/img/ducatus-logo-first.png"
                  width="150"
                  height="150"
                  border="0"
                  alt=""
                />
              </td>
            </tr>
            <tr>
              <td class="innerpadding" style="padding-bottom: 5px;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                  <tr>
                    <td class="accent">Thank you for purchasing DUC.</td>
                  </tr>
                  <tr>
                    <td class="body-text">
                      We have received your payment and you will receive
                      <span class="text-heavy-underline">{duc_amount}</span> in your
                      wallet soon.
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td
                class="bg-lightpink innerpadding"
                style="padding: 20px 0px 10px 0px;"
              >
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                  <tr>
                    <td class="body-text ta-c">
                      Don't miss this once in a lifetime chance!
                    </td>
                  </tr>
                  <tr>
                    <td class="body-text ta-c">
                      Stand a chance to win a limited-edition luxury watch worth
                      $329,000 on your next DUC purchase.<br />
                      Buy a minimum $10 to get 1 entry plus extra Digital
                      Shopping Voucher and Discount Voucher at our e-Commerce
                      site
                      <a href="https://remusnation.com/dshop/" class="body-link"
                        >https://remusnation.com/dshop/</a
                      >
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td class="spacer"></td>
            </tr>
            <tr>
              <td class="body-text ta-c" style="padding-bottom: 5px;">
                The more DUC you buy, the more chances you get.
              </td>
            </tr>
            <tr>
              <td class="spacer"></td>
            </tr>
            <tr>
              <td class="ta-c">
                <a class="btn" href="https://www.ducatuscoins.com/buy/"
                  >BUY AGAIN</a
                >
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
</html>
"""
