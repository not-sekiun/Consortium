import argparse

parser = argparse.ArgumentParser(description="Example Argument Parser")

# parser.add_argument(
#     "a",
#     nargs=1,
# )
# parser.add_argument(
#     "b",
#     nargs=1,
# )
# parser.add_argument(
#     "c",
#     nargs="*",
# )
parser.add_argument(
    "d",
    nargs="?",
)
p = parser.parse_args()
# print(getattr(p, "a"))
# print(getattr(p, "b"))
# print(getattr(p, "c"))
print(p.d)
