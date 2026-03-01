import { useState } from 'react';

interface MenuInputProps {
  readonly onSubmit: (menuText: string, restaurantName: string) => void;
  readonly isLoading: boolean;
}

const SAMPLE_MENU = `Bombay Palace Indian Restaurant

APPETIZERS
Samosa (2 pcs) .............. $6.99
Crispy pastry filled with spiced potatoes and peas
Vegetable Pakora ............ $7.99
Assorted vegetables dipped in chickpea batter and fried
Chicken Tikka ............... $12.99
Boneless chicken marinated in yogurt and spices, grilled in tandoor
Paneer Tikka (V) ............ $11.99
Cottage cheese marinated and grilled

MAIN COURSE - CHICKEN
Butter Chicken .............. $17.99
Tender chicken in creamy tomato sauce
Chicken Tikka Masala ........ $18.99
Grilled chicken in rich masala gravy
Chicken Korma ............... $17.99
Chicken cooked in mild cashew and cream sauce

MAIN COURSE - VEGETARIAN
Palak Paneer (V) ............ $15.99
Cottage cheese in creamy spinach sauce
Chana Masala (V) ............ $13.99
Chickpeas in spiced tomato gravy
Dal Makhani (V) ............. $14.99
Slow-cooked black lentils in butter and cream

BREADS
Naan ....................... $3.99
Garlic Naan ................ $4.99

DESSERTS
Gulab Jamun ................ $5.99
Rasmalai ................... $6.99`;

export default function MenuInput({ onSubmit, isLoading }: MenuInputProps) {
  const [menuText, setMenuText] = useState('');
  const [restaurantName, setRestaurantName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (menuText.trim().length >= 20) {
      onSubmit(menuText, restaurantName || 'Unknown');
    }
  };

  const loadSample = () => {
    setMenuText(SAMPLE_MENU);
    setRestaurantName('Bombay Palace');
  };

  return (
    <form onSubmit={handleSubmit} className="menu-input">
      <div className="input-header">
        <h2>Paste a Menu</h2>
        <button type="button" className="btn-secondary" onClick={loadSample}>
          Load Sample Menu
        </button>
      </div>

      <div className="field">
        <label htmlFor="restaurant-name">Restaurant Name (optional)</label>
        <input
          id="restaurant-name"
          type="text"
          placeholder="e.g. Bombay Palace"
          value={restaurantName}
          onChange={(e) => setRestaurantName(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="menu-text">Menu Content</label>
        <textarea
          id="menu-text"
          placeholder="Paste the restaurant menu text here..."
          value={menuText}
          onChange={(e) => setMenuText(e.target.value)}
          rows={16}
        />
        <span className="char-count">{menuText.length} characters</span>
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={isLoading || menuText.trim().length < 20}
      >
        {isLoading ? (
          <>
            <span className="spinner" />
            Extracting with LFM2...
          </>
        ) : (
          'Extract Menu →'
        )}
      </button>
    </form>
  );
}
