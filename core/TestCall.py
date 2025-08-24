from AHKRPC import call

print("Add(2, 3) =", call("Add", 2, 3))  # 5
print("Bold('xyz') =", call("Latex.ToggleBold", "xyz"))  # \mathbf{xyz}
