from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

def sendEmail(blocked, timedOut, badAuth, commits):

    # Begin by defining the email / SMTP details.
    port = 25
    smtpServer = "smtp.domain.com"
    email = MIMEMultipart()
    email['From'] = "deviceBackup@domain.com"
    email['To'] = "targetEmail@domain.com"
    email['Subject'] = "Device Backups for " + str(date.today())
    
    # Define the HTML document
    html = """\
    <html>
        <body>
            <font face = "Calibri">
                <h1>Failed Backup Hosts!</h1>
                <p>If a host appears under "Blocked", this host actively denied an SSH connection. Check firewall policies and SSH access rules.</p>
                <p>If a host appears under "Timed Out", this host simply timed out and was out of reach at the time of execution.</p>
                <p>If a host appears under "Authentication Failed", this host had incorrect login credentials.</p>
                <table style="border:1px solid black">
                    <tr>
                        <th style="text-align: center; border-bottom:1px solid black;">
                            Blocked
                        </th>
                        <th style="text-align: center; border-bottom:1px solid black;">
                            Timed Out
                        </th>
                        <th style="text-align: center; border-bottom:1px solid black;">
                            Authentication Failed
                        </th>
                    </tr>
                    <tr>
    """

    for i in range(max(len(blocked), len(timedOut), len(badAuth))):
        try:
            html += "<td style=\"text-align: center\">" + blocked[i] + "</td>"
            html += "<td style=\"text-align: center\">" + timedOut[i] + "</td>" 
            html += "<td style=\"text-align: center\">" + badAuth[i] + "</td>" 
        except IndexError:
            html += "<td>&nbsp;</td>"
            if i >= len(blocked):
                if i < len(timedOut) and i < len(badAuth):
                    html += "<td style=\"text-align: center\">" + timedOut[i] + "</td>"
                    html += "<td style=\"text-align: center\">" + badAuth[i] + "</td>"
                elif i < len(timedOut) and i >= len(badAuth):
                    html += "<td style=\"text-align: center\">" + timedOut[i] + "</td>"
                    html += "<td>&nbsp;</td>"
                elif i >= len(timedOut) and i < len(badAuth):
                    html += "<td>&nbsp;</td>"
                    html += "<td style=\"text-align: center\">" + badAuth[i] + "</td>"
            elif i >= len(timedOut):
                if i < len(badAuth):
                    html += "<td style=\"text-align: center\">" + badAuth[i] + "</td>"
                else:
                    html += "<td>&nbsp;</td>"
        finally:
            html += "</tr>"

    html += """\
                </table>
                <hr>
                <h1> Git Commit Statuses </h1>
                <h2> Routers </h2>
    """
    html += "<p>" + str(commits['Routers']) + "</p>"
    html += "<h2> Switches </h2>"
    html += "<p>" + str(commits['Switches']) + "</p>"
    html += "<h2> Firewalls </h2>"
    html += "<p>" + str(commits['Firewalls']) + "</p>"
    html += "<h2> Voice </h2>"
    html += "<p>" + str(commits['Voice']) + "</p>"
    html += "<h2> Wireless </h2>"
    html += "<p>" + str(commits['Wireless']) + "</p>"
    html += """\
            </font>
        </body>
    </html>
    """

    email.attach(MIMEText(html, "html"))

    with SMTP(smtpServer, port) as server:
        server.sendmail(email['From'], email['To'], email.as_string())
    print('Sent as email')