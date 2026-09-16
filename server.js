const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const DB_FILE = './products.json';

app.use(express.json());
app.use(express.static('public'));

// Helper functions for JSON database
function getProducts() {
  if (!fs.existsSync(DB_FILE)) fs.writeFileSync(DB_FILE, JSON.stringify([]));
  try {
    return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
  } catch (e) {
    return [];
  }
}

function saveProducts(data) {
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

// APIs
app.get('/api/products', (req, res) => {
  res.json(getProducts());
});

app.post('/api/products', (req, res) => {
  const { name, size_mm, size_inch, weight, price } = req.body;
  const products = getProducts();
  const newProduct = {
    id: Date.now(),
    name,
    size_mm,
    size_inch,
    weight,
    price: Number(price)
  };
  products.push(newProduct);
  saveProducts(products);
  res.json({ success: true, product: newProduct });
});

app.post('/api/orders', (req, res) => {
  const orderId = Date.now();
  res.json({ orderId });
});

app.listen(3000, () => {
  console.log('Arfa Trading server running at http://localhost:3000');
});
