def total(a,b):

    return a*b

number=int(input("수량을 입력하시오: "))
price=int(input("물품의 가격을 입력하시오: "))

print("수량: ", number)
print("가격: ", price)
print("총합: ", total(number,price))