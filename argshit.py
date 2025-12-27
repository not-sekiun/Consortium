from rich.console import Console
from rich.table import Table

console = Console()

# Calculate totals beforehand as the footer is added with the columns
total_items = 5
total_price = 199.95

# 1. Instantiate the table with show_footer=True
table = Table(
    title="Shopping Cart",
    caption="asdasd",
    show_footer=True,
    footer_style="bold magenta",
)

# 2. Add columns, specifying the footer content in the 'footer' argument
table.add_column("Item", justify="right", footer="Total")
table.add_column("Quantity", justify="right", footer=str(total_items))
table.add_column("Price", justify="right", style="green", footer=f"${total_price:.2f}")

# 3. Add the main rows of data
table.add_row("Laptop", "1", "$99.99")
table.add_row("Mouse", "2", "$19.99")
table.add_row("Keyboard", "1", "$79.98")
table.add_row("Monitor", "1", "$0.00")  # Free item to reach total

# 4. Print the table to the console
console.print(table)
