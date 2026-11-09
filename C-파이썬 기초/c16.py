def f_to_c(f):
    """화씨 숫자를 받아 섭씨 숫자를 돌려줍니다."""
    # 첫 문자열은 함수 설명인 docstring입니다.
    return (f - 32) * 5 / 9

result = f_to_c(72)
print(f"변환 결과: {result:.1f}")
print(f"어는점: {f_to_c(32):.1f}")
# 같은 처리 절차를 값만 바꿔 여러 번 사용합니다.