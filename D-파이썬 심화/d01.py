def delivery_fee(amount):
    # amount는 함수에 전달된 주문 금액을 받는 매개변수입니다.
    if amount >= 30000:
        # 무료 배송이어도 숫자 0을 반환합니다. None을 반환하는 것과 다릅니다.
        return 0
    # 위에서 반환하지 않았을 때만 이 줄에 도착합니다.
    return 3000

def payment(amount):
    # 함수의 반환값을 다른 계산에 사용할 수 있습니다.
    fee = delivery_fee(amount)
    return amount + fee

# 호출할 때 전달하는 실제 값 25000과 30000을 인수라고 합니다.
for amount in [25000, 30000]:
    fee = delivery_fee(amount)
    total = payment(amount)
    print(f"주문 {amount} / 배송 {fee} / 결제 {total}")