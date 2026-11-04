class EntityNotFoundError(Exception):
    pass


class EntityAlreadyExistsError(Exception):
    pass


class BusinessRuleError(Exception):
    pass


class AccountDisabledError(Exception):
    pass
