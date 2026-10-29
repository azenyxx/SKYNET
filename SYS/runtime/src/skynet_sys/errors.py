CODES = frozenset(('INVALID_SCHEMA','UNSUPPORTED_VERSION','INVALID_IDENTITY','CAPABILITY_DENIED','INVALID_TRANSITION','DUPLICATE_MESSAGE','EXPIRED_MESSAGE','INVALID_DIGEST','EVIDENCE_UNAVAILABLE','INTERNAL_ERROR'))
class ContractError(ValueError):
    def __init__(self, code):
        self.code = code if type(code) is str and code in CODES else 'INTERNAL_ERROR'
        super().__init__(self.code)
def need(condition, code='INVALID_SCHEMA'):
    if not condition: raise ContractError(code)
