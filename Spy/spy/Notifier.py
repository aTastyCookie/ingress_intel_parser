import requests


class MailNotifier:
    def __init__(self, alert_email, sandbox, apikey):
        self.email = alert_email
        self.sandbox = sandbox
        self.apikey = apikey

    def send(self, subject, message):
        return requests.post(
            "https://api.mailgun.net/v3/%s.mailgun.org/messages" % self.sandbox,
            auth=("api", self.apikey),
            data={"from": "Excited User <mailgun@%s.mailgun.org>" % self.sandbox,
                  "to": [self.email],
                  "subject": "[Ingress daemon] %s" % subject,
                  "text": message})

    def handleException(self, e):
        return self.send('Here some exception', e.message)

# m = MailNotifier('alistar.neron@gmail.com', 'sandboxa4e8d50aae734576b294351bbd7e1c54', 'key-2f503566cff2978c07a967dd6438817b')
# from ingress.exceptions.AccountBanned import AccountBannedException
# m.handleException(AccountBannedException('alistar.neron@gmail.com'))