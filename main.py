doc = """
I AM SOME DOCS
"""
doc2 = """
I AM ALSO SOME DOCS
"""


def a():
    f"""
{doc}
{doc2}
    """
    print(1)


a()
