from scripts.players.model import Model

m1 = Model("resources/chess-o1")
m2 = Model("resources/chess-q1")
m3 = Model("resources/chess-o1")

print(m1.path)
print(m2.path)
print(m1 is m2)
print(m1 is m3)

print(m1.check("resources/chess-o1"))
print(m2.check("resources/chess-q1"))
print(m1.check("resources/chess-q1"))

print(m1.generate("e2e4"))
print(m2.generate("e2e4"))
print(m3.generate("e2e4"))