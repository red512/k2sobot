"""
US Presidents information tools
"""

def get_us_presidents():
    """
    Get information about all US Presidents by years of service

    Returns a list of all US Presidents with their terms in office
    """
    presidents = [
        {"name": "George Washington", "years": "1789-1797", "number": 1, "party": "Independent"},
        {"name": "John Adams", "years": "1797-1801", "number": 2, "party": "Federalist"},
        {"name": "Thomas Jefferson", "years": "1801-1809", "number": 3, "party": "Democratic-Republican"},
        {"name": "James Madison", "years": "1809-1817", "number": 4, "party": "Democratic-Republican"},
        {"name": "James Monroe", "years": "1817-1825", "number": 5, "party": "Democratic-Republican"},
        {"name": "John Quincy Adams", "years": "1825-1829", "number": 6, "party": "Democratic-Republican"},
        {"name": "Andrew Jackson", "years": "1829-1837", "number": 7, "party": "Democratic"},
        {"name": "Martin Van Buren", "years": "1837-1841", "number": 8, "party": "Democratic"},
        {"name": "William Henry Harrison", "years": "1841", "number": 9, "party": "Whig"},
        {"name": "John Tyler", "years": "1841-1845", "number": 10, "party": "Whig"},
        {"name": "James K. Polk", "years": "1845-1849", "number": 11, "party": "Democratic"},
        {"name": "Zachary Taylor", "years": "1849-1850", "number": 12, "party": "Whig"},
        {"name": "Millard Fillmore", "years": "1850-1853", "number": 13, "party": "Whig"},
        {"name": "Franklin Pierce", "years": "1853-1857", "number": 14, "party": "Democratic"},
        {"name": "James Buchanan", "years": "1857-1861", "number": 15, "party": "Democratic"},
        {"name": "Abraham Lincoln", "years": "1861-1865", "number": 16, "party": "Republican"},
        {"name": "Andrew Johnson", "years": "1865-1869", "number": 17, "party": "Democratic"},
        {"name": "Ulysses S. Grant", "years": "1869-1877", "number": 18, "party": "Republican"},
        {"name": "Rutherford B. Hayes", "years": "1877-1881", "number": 19, "party": "Republican"},
        {"name": "James A. Garfield", "years": "1881", "number": 20, "party": "Republican"},
        {"name": "Chester A. Arthur", "years": "1881-1885", "number": 21, "party": "Republican"},
        {"name": "Grover Cleveland", "years": "1885-1889", "number": 22, "party": "Democratic"},
        {"name": "Benjamin Harrison", "years": "1889-1893", "number": 23, "party": "Republican"},
        {"name": "Grover Cleveland", "years": "1893-1897", "number": 24, "party": "Democratic"},
        {"name": "William McKinley", "years": "1897-1901", "number": 25, "party": "Republican"},
        {"name": "Theodore Roosevelt", "years": "1901-1909", "number": 26, "party": "Republican"},
        {"name": "William Howard Taft", "years": "1909-1913", "number": 27, "party": "Republican"},
        {"name": "Woodrow Wilson", "years": "1913-1921", "number": 28, "party": "Democratic"},
        {"name": "Warren G. Harding", "years": "1921-1923", "number": 29, "party": "Republican"},
        {"name": "Calvin Coolidge", "years": "1923-1929", "number": 30, "party": "Republican"},
        {"name": "Herbert Hoover", "years": "1929-1933", "number": 31, "party": "Republican"},
        {"name": "Franklin D. Roosevelt", "years": "1933-1945", "number": 32, "party": "Democratic"},
        {"name": "Harry S. Truman", "years": "1945-1953", "number": 33, "party": "Democratic"},
        {"name": "Dwight D. Eisenhower", "years": "1953-1961", "number": 34, "party": "Republican"},
        {"name": "John F. Kennedy", "years": "1961-1963", "number": 35, "party": "Democratic"},
        {"name": "Lyndon B. Johnson", "years": "1963-1969", "number": 36, "party": "Democratic"},
        {"name": "Richard Nixon", "years": "1969-1974", "number": 37, "party": "Republican"},
        {"name": "Gerald Ford", "years": "1974-1977", "number": 38, "party": "Republican"},
        {"name": "Jimmy Carter", "years": "1977-1981", "number": 39, "party": "Democratic"},
        {"name": "Ronald Reagan", "years": "1981-1989", "number": 40, "party": "Republican"},
        {"name": "George H.W. Bush", "years": "1989-1993", "number": 41, "party": "Republican"},
        {"name": "Bill Clinton", "years": "1993-2001", "number": 42, "party": "Democratic"},
        {"name": "George W. Bush", "years": "2001-2009", "number": 43, "party": "Republican"},
        {"name": "Barack Obama", "years": "2009-2017", "number": 44, "party": "Democratic"},
        {"name": "Donald Trump", "years": "2017-2021", "number": 45, "party": "Republican"},
        {"name": "Joe Biden", "years": "2021-present", "number": 46, "party": "Democratic"}
    ]

    return {
        "total_presidents": len(presidents),
        "presidents": presidents
    }


def get_president_by_year(year):
    """
    Get the US President who was in office during a specific year

    Args:
        year (int): The year to check (e.g., 1863, 2020)

    Returns:
        dict: Information about the president in office during that year
    """
    presidents = get_us_presidents()["presidents"]

    try:
        year = int(year)
    except (ValueError, TypeError):
        return {"error": "Please provide a valid year as a number"}

    for president in presidents:
        years = president["years"]
        if "-" in years:
            start_year, end_year = years.split("-")
            start_year = int(start_year)
            if "present" in end_year:
                end_year = 2025  # Current year
            else:
                end_year = int(end_year)

            if start_year <= year <= end_year:
                return president
        else:
            # Single year presidency (like William Henry Harrison)
            if int(years) == year:
                return president

    return {"error": f"No president found for year {year}. US presidents started serving in 1789."}


def get_longest_serving_president():
    """
    Get information about the US President who served the longest

    Returns:
        dict: Information about Franklin D. Roosevelt and his terms
    """
    return {
        "name": "Franklin D. Roosevelt",
        "years": "1933-1945",
        "number": 32,
        "party": "Democratic",
        "terms": 4,
        "years_served": 12,
        "note": "Only president to serve more than two terms, died in office during his 4th term"
    }