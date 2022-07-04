from django import template
register = template.Library()


class Test:
    def __init__(self):
        self.name = "test"


@register.filter
def get_attr(obj, val):
    return getattr(obj, val, False)


if __name__ == "__main__":
    test_user = Test()
    print(get_attr(test_user, 'name'))