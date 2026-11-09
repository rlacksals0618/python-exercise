def calculate_total(price, quantity, delivery=0, discount=0):
    # price와 quantity는 호출할 때마다 새로 받는 함수 안의 이름입니다.
    # delivery를 생략하면 기본값 0을 사용합니다.
    total = price * quantity + delivery - discount
    return total

# 같은 계산 규칙을 서로 다른 입력에 적용합니다.
pickup = calculate_total(2000, 3)
shipped = calculate_total(2000, 3, delivery=1000)
# 이름을 지정하면 인수 순서를 바꿔도 뜻이 드러납니다.
named = calculate_total(quantity=2, price=1500, delivery=500)

print(f"방문 수령: {pickup}")
print(f"배송: {shipped}")
print(f"다른 주문: {named}")

# 직접 작성: 할인 금액 discount=0을 인수로 더하고 계산하세요.