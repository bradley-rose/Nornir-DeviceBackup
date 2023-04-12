def writeToFile(*, blocked, timedOut, badAuth, commits):
    # Define the HTML document
    html = """\
    <hr>
    <h1>Device Backup</h1>
    <p>If a host appears under "Blocked", this host actively denied an SSH connection. Check firewall policies and local SSH access rules.</p>
    <p>If a host appears under "Timed Out", this host simply timed out and was either dropped by a firewall policy, or simply offline at the time of execution.</p>
    <p>If a host appears under "Authentication Failed", the backup job does not have the correct credentials for the device.</p>
    <table style="width:100%">
        <tr>
            <th style="text-align: center">
                Blocked
            </th>
            <th style="text-align: center">
                Timed Out
            </th>
            <th style="text-align: center">
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
    <h2> Backup Directory Git Commit Status </h2>
    <h3> Routers </h3>
    """
    html += "<p>" + str(commits['Routers']) + "</p>"
    html += "<h3> Switches </h3>"
    html += "<p>" + str(commits['Switches']) + "</p>"
    html += "<h3> Firewalls </h3>"
    html += "<p>" + str(commits['Firewalls']) + "</p>"
    html += "<h3> Voice </h3>"
    html += "<p>" + str(commits['Voice']) + "</p>"
    html += "<h3> WLCs </h3>"
    html += "<p>" + str(commits['WLCs']) + "</p>"

    with open("backupResults.html", "w") as backupResults:
        backupResults.write(html)