from spy.exceptions.Ingress import IngressException


class AccountBannedException(IngressException):
    def __init__(self, email):
        self.message = "Seems like account %s banned" % email

    def __str__(self):
        return repr(self.message)
