from aurite import Aurite

# Singleton instance
_aurite_instance = Aurite()

def get_aurite():
    """Returns the singleton Aurite instance."""
    return _aurite_instance

