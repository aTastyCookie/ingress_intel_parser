from spy.exceptions.Ingress import IngressException


class AccountBannedException(IngressException):
    def __init__(self, id):
        self.message = "Seems like account with _id %s banned" % id