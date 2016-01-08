from spy.exceptions.Ingress import IngressException


class AccountExpiresException(IngressException):
    def __init__(self, id):
        self.message = "Seems like account with _id %s expires" % id

    def __str__(self):
        return repr(self.message)
