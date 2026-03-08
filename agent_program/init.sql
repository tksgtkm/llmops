CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    salary INTEGER,
    hire_date DATE
);

INSERT INTO employees VALUES
(1, 'Tanaka Taro', 'IT', 600000, '2020-04-01'),
(2, 'Yamada Hanako', 'HR', 550000, '2019-03-15'),
(3, 'Suzuki Ichiro', 'Finance', 700000, '2021-01-20'),
(4, 'Watanabe Yuki', 'IT', 650000, '2020-07-10'),
(5, 'Kato Akira', 'Marketing', 580000, '2022-02-01'),
(6, 'Nakamura Yui', 'IT', 620000, '2021-05-15'),
(7, 'Yoshida Saki', 'Finance', 680000, '2020-12-01'),
(8, 'Matsumoto Ryu', 'HR', 540000, '2022-08-20'),
(9, 'Inoue Kana', 'Marketing', 590000, '2021-11-10'),
(10, 'Takahashi Ken', 'IT', 710000, '2019-09-05');

SELECT 'データベースの初期化が完了しました。従業員数:' AS message,
       COUNT(*) AS count
FROM employees;