A = 50
print('Amount Due: 50')
x = int(input('Insert Coin:' ))
if x == 25 or x == 15 or x == 10 or x == 5:
    print('Amount Due:', A-x)
elif x == 30:
    print('Amount Due:', A)

