import streamlit as st
import duckdb
import pandas as pd
import time

# DuckDB 연결 -----------------------------------------------------------------
@st.cache_resource
def get_conn():
    return duckdb.connect("madang.db")  

def query(sql, as_df=False):
    conn = get_conn()
    res = conn.execute(sql)
    return res.df() if as_df else res.fetchall()

# 책 목록 불러오기 ------------------------------------------------------------- 
books = [None]
book_df = query("SELECT bookid, bookname FROM Book ORDER BY bookid", as_df=True)
for _, row in book_df.iterrows():
    books.append(f"{row['bookid']},{row['bookname']}")

# 탭 UI ------------------------------------------------------------------------
tab1, tab2 = st.tabs(["고객조회", "거래 입력"])

name = ""
custid = None
result_df = pd.DataFrame()
name = tab1.text_input("고객명")
select_book = ""

# ------------------------ [탭1] 고객조회 --------------------------------------
if len(name) > 0:
    # 주문 내역 조인 조회 (이름으로)
    sql = f"""
        SELECT 
            c.custid,
            c.name,
            b.bookname,
            o.orderdate,
            o.saleprice
        FROM Customer c
        JOIN Orders o ON c.custid = o.custid
        JOIN Book b   ON o.bookid = b.bookid
        WHERE c.name = '{name}'
        ORDER BY o.orderdate
    """
    result_df = query(sql, as_df=True)

    if result_df.empty:
        tab1.info("이 고객의 주문 내역이 없습니다.")
        # 그래도 custid는 Customer 테이블에서 가져오기
        cust_df = query(
            f"SELECT custid FROM Customer WHERE name = '{name}'",
            as_df=True
        )
        if not cust_df.empty:
            custid = int(cust_df.loc[0, "custid"])
    else:
        tab1.write(result_df)
        custid = int(result_df.loc[0, "custid"])

    # -------------------- [탭2] 거래 입력 ------------------------------------
    if custid is not None:
        tab2.write(f"고객번호: {custid}")
        tab2.write(f"고객명: {name}")
        select_book = tab2.selectbox("구매 서적:", books)

        if select_book:
            bookid = int(select_book.split(",")[0])
            dt = time.strftime('%Y-%m-%d', time.localtime())

            # 다음 orderid 계산
            new_id_df = query(
                "SELECT COALESCE(MAX(orderid) + 1, 1) AS new_id FROM Orders",
                as_df=True
            )
            orderid = int(new_id_df.loc[0, "new_id"])

            price = tab2.text_input("금액", value="0")

            if tab2.button('거래 입력'):
                conn = get_conn()
                conn.execute(
                    """
                    INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [orderid, custid, bookid, int(price), dt]
                )
                tab2.success('거래가 입력되었습니다.')
    else:
        tab2.warning("존재하지 않는 고객입니다. 먼저 Customer 테이블에 고객을 등록하세요.")
