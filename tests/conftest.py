"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_menu_html() -> str:
    """Sample restaurant menu HTML for testing."""
    return """
    <html>
    <body>
    <nav>Navigation here</nav>
    <div class="menu">
        <h2>Appetizers</h2>
        <div class="menu-item">
            <span class="name">Samosa (2 pcs)</span>
            <span class="price">$6.99</span>
            <p>Crispy pastry filled with spiced potatoes and peas</p>
        </div>
        <div class="menu-item">
            <span class="name">Chicken Tikka</span>
            <span class="price">$12.99</span>
            <p>Boneless chicken marinated in yogurt and spices, grilled in tandoor</p>
        </div>
        <h2>Main Course</h2>
        <div class="menu-item">
            <span class="name">Butter Chicken</span>
            <span class="price">$17.99</span>
            <p>Tender chicken in creamy tomato sauce</p>
        </div>
        <div class="menu-item">
            <span class="name">Chicken Tikka Masala</span>
            <span class="price">$18.99</span>
            <p>Grilled chicken in rich masala gravy</p>
        </div>
        <div class="menu-item">
            <span class="name">Palak Paneer</span>
            <span class="price">$15.99</span>
            <span class="tag">V</span>
            <p>Cottage cheese in creamy spinach sauce</p>
        </div>
        <div class="menu-item">
            <span class="name">Dal Makhani</span>
            <span class="price">$14.99</span>
            <span class="tag">V</span>
            <p>Slow-cooked black lentils in butter and cream</p>
        </div>
        <h2>Breads</h2>
        <div class="menu-item">
            <span class="name">Naan</span>
            <span class="price">$3.99</span>
        </div>
        <div class="menu-item">
            <span class="name">Garlic Naan</span>
            <span class="price">$4.99</span>
        </div>
    </div>
    <footer>Footer content</footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_menu_text() -> str:
    """Sample plain text menu (from PDF extraction)."""
    return """
    Taj Mahal Indian Restaurant

    APPETIZERS
    Samosa (2 pcs) .......... $6.99
    Vegetable Pakora ........ $7.99
    Chicken Tikka ........... $12.99

    ENTREES
    Butter Chicken .......... $17.99
    Chicken Tikka Masala .... $18.99
    Lamb Rogan Josh ......... $19.99
    Palak Paneer (V) ........ $15.99
    Chana Masala (V) ........ $13.99

    BREADS
    Naan .................... $3.99
    Garlic Naan ............. $4.99
    Roti .................... $2.99

    DESSERTS
    Gulab Jamun ............. $5.99
    Rasmalai ................ $6.99
    """
