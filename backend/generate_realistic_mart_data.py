import os
import pandas as pd

ITEMS = [
    # --- Staples & Edible Oils ---
    {
        "product_id": "SKU_STP_01",
        "name": "Fortune Sunlite Refined Sunflower Oil (1L)",
        "category": "Staples & Oils",
        "brand": "Fortune",
        "stock_quantity": 180,
        "cost_price": 128.0,
        "selling_price": 155.0,
        "weekly_sales_avg": 42,
        "expiry_days": 270,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_STP_02",
        "name": "Aashirvaad Superior MP Sharbati Atta (5kg)",
        "category": "Staples & Oils",
        "brand": "Aashirvaad",
        "stock_quantity": 120,
        "cost_price": 220.0,
        "selling_price": 275.0,
        "weekly_sales_avg": 38,
        "expiry_days": 180,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_STP_03",
        "name": "India Gate Classic Aged Basmati Rice (5kg)",
        "category": "Staples & Oils",
        "brand": "India Gate",
        "stock_quantity": 65,
        "cost_price": 540.0,
        "selling_price": 675.0,
        "weekly_sales_avg": 19,
        "expiry_days": 365,
        "customer_name": "Ananya Rao",
        "customer_phone": "+91 98459 66778",
        "customer_segment": "High Basket AOV VIP"
    },
    {
        "product_id": "SKU_STP_04",
        "name": "Tata Salt Vacuum Evaporated Iodized Salt (1kg)",
        "category": "Staples & Oils",
        "brand": "Tata",
        "stock_quantity": 250,
        "cost_price": 21.0,
        "selling_price": 28.0,
        "weekly_sales_avg": 65,
        "expiry_days": 730,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_STP_05",
        "name": "24 Mantra Organic Unpolished Toor Dal (1kg)",
        "category": "Staples & Oils",
        "brand": "24 Mantra",
        "stock_quantity": 90,
        "cost_price": 142.0,
        "selling_price": 185.0,
        "weekly_sales_avg": 24,
        "expiry_days": 210,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Organic & Health Conscious"
    },
    {
        "product_id": "SKU_STP_06",
        "name": "Saffola Gold Pro Healthy Lifestyle Oil (5L Jar)",
        "category": "Staples & Oils",
        "brand": "Saffola",
        "stock_quantity": 40,
        "cost_price": 810.0,
        "selling_price": 995.0,
        "weekly_sales_avg": 12,
        "expiry_days": 240,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "High Basket AOV VIP"
    },
    {
        "product_id": "SKU_STP_07",
        "name": "Everest Pure Turmeric Powder / Haldi (500g)",
        "category": "Staples & Oils",
        "brand": "Everest",
        "stock_quantity": 110,
        "cost_price": 95.0,
        "selling_price": 130.0,
        "weekly_sales_avg": 31,
        "expiry_days": 360,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Traditional Kitchen Staples"
    },
    {
        "product_id": "SKU_STP_08",
        "name": "Madhur Pure & Hygienic Refined Sugar (5kg)",
        "category": "Staples & Oils",
        "brand": "Madhur",
        "stock_quantity": 140,
        "cost_price": 210.0,
        "selling_price": 260.0,
        "weekly_sales_avg": 35,
        "expiry_days": 365,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Weekly Pantry Staples"
    },

    # --- Dairy & Chilled Essentials ---
    {
        "product_id": "SKU_DRY_01",
        "name": "Nandini Pure Cow Ghee (1L Pouch)",
        "category": "Dairy",
        "brand": "Nandini",
        "stock_quantity": 85,
        "cost_price": 510.0,
        "selling_price": 630.0,
        "weekly_sales_avg": 34,
        "expiry_days": 180,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Traditional Sweets & Ghee"
    },
    {
        "product_id": "SKU_DRY_02",
        "name": "Amul Fresh Malai Paneer (200g Block)",
        "category": "Dairy",
        "brand": "Amul",
        "stock_quantity": 55,
        "cost_price": 72.0,
        "selling_price": 92.0,
        "weekly_sales_avg": 48,
        "expiry_days": 18,
        "customer_name": "Priya Menon",
        "customer_phone": "+91 98459 22334",
        "customer_segment": "Fresh Chilled Daily"
    },
    {
        "product_id": "SKU_DRY_03",
        "name": "Mother Dairy Pasteurised Table Butter (500g)",
        "category": "Dairy",
        "brand": "Mother Dairy",
        "stock_quantity": 70,
        "cost_price": 215.0,
        "selling_price": 275.0,
        "weekly_sales_avg": 29,
        "expiry_days": 60,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Bakers & Dairy Enthusiasts"
    },
    {
        "product_id": "SKU_DRY_04",
        "name": "Milky Mist Natural Greek Yogurt (400g Tub)",
        "category": "Dairy",
        "brand": "Milky Mist",
        "stock_quantity": 42,
        "cost_price": 85.0,
        "selling_price": 120.0,
        "weekly_sales_avg": 16,
        "expiry_days": 21,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Organic & Health Conscious"
    },
    {
        "product_id": "SKU_DRY_05",
        "name": "Britannia Processed Cheese Slices (10 Slices, 200g)",
        "category": "Dairy",
        "brand": "Britannia",
        "stock_quantity": 60,
        "cost_price": 125.0,
        "selling_price": 165.0,
        "weekly_sales_avg": 22,
        "expiry_days": 120,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Breakfast Essentials"
    },

    # --- Dry Fruits & Nuts (High Margin Anchors) ---
    {
        "product_id": "SKU_NUT_01",
        "name": "Nutraj California Premium Whole Almonds (500g)",
        "category": "Dry Fruits",
        "brand": "Nutraj",
        "stock_quantity": 60,
        "cost_price": 340.0,
        "selling_price": 490.0,
        "weekly_sales_avg": 22,
        "expiry_days": 270,
        "customer_name": "Ananya Rao",
        "customer_phone": "+91 98459 66778",
        "customer_segment": "Festive Gifting & Dry Fruits"
    },
    {
        "product_id": "SKU_NUT_02",
        "name": "Royal Harvest Jumbo Roasted & Salted Pistachios (250g)",
        "category": "Dry Fruits",
        "brand": "Royal Harvest",
        "stock_quantity": 45,
        "cost_price": 230.0,
        "selling_price": 340.0,
        "weekly_sales_avg": 15,
        "expiry_days": 240,
        "customer_name": "Priya Menon",
        "customer_phone": "+91 98459 22334",
        "customer_segment": "Festive Gifting & Dry Fruits"
    },
    {
        "product_id": "SKU_NUT_03",
        "name": "Tata Sampann 100% Pure Whole Cashews W320 (500g)",
        "category": "Dry Fruits",
        "brand": "Tata Sampann",
        "stock_quantity": 50,
        "cost_price": 410.0,
        "selling_price": 575.0,
        "weekly_sales_avg": 18,
        "expiry_days": 300,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Traditional Sweets & Ghee"
    },
    {
        "product_id": "SKU_NUT_04",
        "name": "Tulsi Afghani Dried Golden Anjeer / Figs (250g)",
        "category": "Dry Fruits",
        "brand": "Tulsi",
        "stock_quantity": 38,
        "cost_price": 240.0,
        "selling_price": 360.0,
        "weekly_sales_avg": 11,
        "expiry_days": 210,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Organic & Health Conscious"
    },
    {
        "product_id": "SKU_NUT_05",
        "name": "Rostaa Gourmet Super 7 Healthy Roasted Seed Mix (200g)",
        "category": "Dry Fruits",
        "brand": "Rostaa",
        "stock_quantity": 35,
        "cost_price": 145.0,
        "selling_price": 225.0,
        "weekly_sales_avg": 14,
        "expiry_days": 180,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Organic & Health Conscious"
    },

    # --- Snacks & Munchies ---
    {
        "product_id": "SKU_SNK_01",
        "name": "Bikaji Royal Bikaneri Bhujia Sev (400g)",
        "category": "Snacks",
        "brand": "Bikaji",
        "stock_quantity": 110,
        "cost_price": 85.0,
        "selling_price": 130.0,
        "weekly_sales_avg": 40,
        "expiry_days": 180,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Impulse Snacking & Beverages"
    },
    {
        "product_id": "SKU_SNK_02",
        "name": "Haldiram's Nagpur All-In-One Mixture (350g)",
        "category": "Snacks",
        "brand": "Haldiram's",
        "stock_quantity": 95,
        "cost_price": 78.0,
        "selling_price": 115.0,
        "weekly_sales_avg": 36,
        "expiry_days": 180,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_SNK_03",
        "name": "Britannia Good Day Butter Rich Cookies (600g Mega Saver)",
        "category": "Snacks",
        "brand": "Britannia",
        "stock_quantity": 130,
        "cost_price": 98.0,
        "selling_price": 145.0,
        "weekly_sales_avg": 46,
        "expiry_days": 210,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "Tea-Time Family Snacks"
    },
    {
        "product_id": "SKU_SNK_04",
        "name": "Mr. Makhana Roasted Pudina & Lime Foxnuts (100g)",
        "category": "Snacks",
        "brand": "Mr. Makhana",
        "stock_quantity": 55,
        "cost_price": 80.0,
        "selling_price": 135.0,
        "weekly_sales_avg": 20,
        "expiry_days": 270,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Organic & Health Conscious"
    },
    {
        "product_id": "SKU_SNK_05",
        "name": "Lay's India's Magic Masala Potato Chips (115g Mega)",
        "category": "Snacks",
        "brand": "Lay's",
        "stock_quantity": 140,
        "cost_price": 32.0,
        "selling_price": 50.0,
        "weekly_sales_avg": 58,
        "expiry_days": 150,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Impulse Snacking & Beverages"
    },

    # --- Beverages (Tea & Coffee) ---
    {
        "product_id": "SKU_BEV_01",
        "name": "Tata Tea Gold Assam CTC & Long Leaf Blend (500g)",
        "category": "Beverages",
        "brand": "Tata Tea",
        "stock_quantity": 105,
        "cost_price": 195.0,
        "selling_price": 265.0,
        "weekly_sales_avg": 39,
        "expiry_days": 365,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "Tea-Time Family Snacks"
    },
    {
        "product_id": "SKU_BEV_02",
        "name": "Bru Instant Coffee Chicory Blend Glass Jar (200g)",
        "category": "Beverages",
        "brand": "Bru",
        "stock_quantity": 75,
        "cost_price": 265.0,
        "selling_price": 360.0,
        "weekly_sales_avg": 27,
        "expiry_days": 540,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Coffee Connoisseurs"
    },
    {
        "product_id": "SKU_BEV_03",
        "name": "Twinings Pure Green Tea Bags with Lemon & Honey (25pk)",
        "category": "Beverages",
        "brand": "Twinings",
        "stock_quantity": 50,
        "cost_price": 180.0,
        "selling_price": 270.0,
        "weekly_sales_avg": 17,
        "expiry_days": 540,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Organic & Health Conscious"
    },
    {
        "product_id": "SKU_BEV_04",
        "name": "Real Fruit Power 100% Alphonso Mango Nectar (1L Tetra)",
        "category": "Beverages",
        "brand": "Real",
        "stock_quantity": 88,
        "cost_price": 92.0,
        "selling_price": 130.0,
        "weekly_sales_avg": 33,
        "expiry_days": 180,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Impulse Snacking & Beverages"
    },

    # --- Sweets, Chocolates & Festive Hampers ---
    {
        "product_id": "SKU_SWT_01",
        "name": "Ferrero Rocher Fine Hazelnut Chocolates Box (16 Pieces)",
        "category": "Sweets & Confectionery",
        "brand": "Ferrero",
        "stock_quantity": 50,
        "cost_price": 380.0,
        "selling_price": 549.0,
        "weekly_sales_avg": 16,
        "expiry_days": 270,
        "customer_name": "Ananya Rao",
        "customer_phone": "+91 98459 66778",
        "customer_segment": "High Basket AOV VIP"
    },
    {
        "product_id": "SKU_SWT_02",
        "name": "Cadbury Celebrations Rich Premium Dry Fruit Box (177g)",
        "category": "Sweets & Confectionery",
        "brand": "Cadbury",
        "stock_quantity": 65,
        "cost_price": 280.0,
        "selling_price": 400.0,
        "weekly_sales_avg": 24,
        "expiry_days": 240,
        "customer_name": "Priya Menon",
        "customer_phone": "+91 98459 22334",
        "customer_segment": "Festive Gifting & Dry Fruits"
    },
    {
        "product_id": "SKU_SWT_03",
        "name": "Haldiram's Prabhuji Pure Desi Ghee Gulab Jamun Tin (1kg)",
        "category": "Sweets & Confectionery",
        "brand": "Haldiram's",
        "stock_quantity": 72,
        "cost_price": 185.0,
        "selling_price": 260.0,
        "weekly_sales_avg": 25,
        "expiry_days": 180,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Traditional Sweets & Ghee"
    },
    {
        "product_id": "SKU_SWT_04",
        "name": "Bikaji Soan Papdi Pure Desi Ghee Flaky Sweet (500g)",
        "category": "Sweets & Confectionery",
        "brand": "Bikaji",
        "stock_quantity": 80,
        "cost_price": 140.0,
        "selling_price": 210.0,
        "weekly_sales_avg": 28,
        "expiry_days": 180,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Weekly Pantry Staples"
    },

    # --- Puja & Festive Speciality ---
    {
        "product_id": "SKU_PUJ_01",
        "name": "Mitti Art Handcrafted Terracotta Oil Deepas (Box of 12)",
        "category": "Puja & Festive",
        "brand": "Mitti Art",
        "stock_quantity": 150,
        "cost_price": 45.0,
        "selling_price": 95.0,
        "weekly_sales_avg": 42,
        "expiry_days": 730,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "Puja & Home Essentials"
    },
    {
        "product_id": "SKU_PUJ_02",
        "name": "Cycle Pure 3-in-1 Fragrance Agarbatti Pooja Pack (250g)",
        "category": "Puja & Festive",
        "brand": "Cycle Pure",
        "stock_quantity": 115,
        "cost_price": 60.0,
        "selling_price": 95.0,
        "weekly_sales_avg": 35,
        "expiry_days": 730,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Puja & Home Essentials"
    },
    {
        "product_id": "SKU_PUJ_03",
        "name": "Mangaldeep Pure Temple Sambrani Dhoop Cups (Pack of 12)",
        "category": "Puja & Festive",
        "brand": "Mangaldeep",
        "stock_quantity": 90,
        "cost_price": 75.0,
        "selling_price": 120.0,
        "weekly_sales_avg": 26,
        "expiry_days": 730,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Puja & Home Essentials"
    },

    # --- Home Hygiene & Personal Care ---
    {
        "product_id": "SKU_HGC_01",
        "name": "Surf Excel Matic Top Load Liquid Detergent Pouch (2L)",
        "category": "Personal Care",
        "brand": "Surf Excel",
        "stock_quantity": 70,
        "cost_price": 310.0,
        "selling_price": 420.0,
        "weekly_sales_avg": 26,
        "expiry_days": 730,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_HGC_02",
        "name": "Dettol Original Germ Protection Liquid Handwash (1500ml Refill)",
        "category": "Personal Care",
        "brand": "Dettol",
        "stock_quantity": 85,
        "cost_price": 155.0,
        "selling_price": 225.0,
        "weekly_sales_avg": 32,
        "expiry_days": 730,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Home Hygiene & Essentials"
    },
    {
        "product_id": "SKU_HGC_03",
        "name": "Vim Dishwash Gel with Real Lemon Power (750ml Bottle)",
        "category": "Personal Care",
        "brand": "Vim",
        "stock_quantity": 110,
        "cost_price": 115.0,
        "selling_price": 160.0,
        "weekly_sales_avg": 44,
        "expiry_days": 730,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Home Hygiene & Essentials"
    },
    {
        "product_id": "SKU_HGC_04",
        "name": "Dabur Red Ayurvedic Toothpaste Mega Saver Pack (300g x 2)",
        "category": "Personal Care",
        "brand": "Dabur",
        "stock_quantity": 75,
        "cost_price": 145.0,
        "selling_price": 210.0,
        "weekly_sales_avg": 28,
        "expiry_days": 540,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "Home Hygiene & Essentials"
    },
    # --- Breakfast & Instant Foods ---
    {
        "product_id": "SKU_FOD_01",
        "name": "Maggi 2-Minute Masala Instant Noodles (12 Pack Saver, 840g)",
        "category": "Snacks",
        "brand": "Maggi",
        "stock_quantity": 140,
        "cost_price": 142.0,
        "selling_price": 180.0,
        "weekly_sales_avg": 62,
        "expiry_days": 240,
        "customer_name": "Rajesh Varma",
        "customer_phone": "+91 98459 55667",
        "customer_segment": "Impulse Snacking & Instant Meals"
    },
    {
        "product_id": "SKU_FOD_02",
        "name": "Kellogg's Real Almond & Honey Crunchy Corn Flakes (1kg Mega)",
        "category": "Staples & Oils",
        "brand": "Kellogg's",
        "stock_quantity": 55,
        "cost_price": 360.0,
        "selling_price": 490.0,
        "weekly_sales_avg": 22,
        "expiry_days": 270,
        "customer_name": "Ananya Rao",
        "customer_phone": "+91 98459 66778",
        "customer_segment": "Healthy Breakfast Family"
    },
    {
        "product_id": "SKU_FOD_03",
        "name": "Quaker Rolled Oats 100% Wholegrain Health Pack (1kg)",
        "category": "Staples & Oils",
        "brand": "Quaker",
        "stock_quantity": 65,
        "cost_price": 155.0,
        "selling_price": 215.0,
        "weekly_sales_avg": 28,
        "expiry_days": 365,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Organic & Health Conscious"
    },
    # --- Regional Spices & Masalas ---
    {
        "product_id": "SKU_SPC_01",
        "name": "Catch Pure Red Chilli Powder / Teekha Lal Mirch (500g)",
        "category": "Staples & Oils",
        "brand": "Catch",
        "stock_quantity": 95,
        "cost_price": 125.0,
        "selling_price": 175.0,
        "weekly_sales_avg": 30,
        "expiry_days": 360,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Weekly Pantry Staples"
    },
    {
        "product_id": "SKU_SPC_02",
        "name": "MDH Famous Deggi Mirch Natural Red Colour Blend (100g)",
        "category": "Staples & Oils",
        "brand": "MDH",
        "stock_quantity": 110,
        "cost_price": 62.0,
        "selling_price": 85.0,
        "weekly_sales_avg": 36,
        "expiry_days": 365,
        "customer_name": "Meera Iyer",
        "customer_phone": "+91 98459 88990",
        "customer_segment": "Traditional Kitchen Staples"
    },
    # --- Chilled Dairy & Sauces ---
    {
        "product_id": "SKU_DRY_06",
        "name": "Amul Taaza Homogenised Toned Milk (1L Tetra Pack)",
        "category": "Dairy",
        "brand": "Amul",
        "stock_quantity": 90,
        "cost_price": 58.0,
        "selling_price": 74.0,
        "weekly_sales_avg": 68,
        "expiry_days": 120,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Daily Chilled Essentials"
    },
    {
        "product_id": "SKU_SNK_06",
        "name": "Kissan 100% Real Fresh Tomato Ketchup (1.2kg Squeezy)",
        "category": "Snacks",
        "brand": "Kissan",
        "stock_quantity": 70,
        "cost_price": 110.0,
        "selling_price": 155.0,
        "weekly_sales_avg": 26,
        "expiry_days": 180,
        "customer_name": "Suresh Babu",
        "customer_phone": "+91 98459 33445",
        "customer_segment": "Tea-Time Family Snacks"
    },
    # --- Confectionery & Premium Mithai ---
    {
        "product_id": "SKU_SWT_05",
        "name": "Cadbury Dairy Milk Silk Roasted Almond Chocolate (143g)",
        "category": "Sweets & Confectionery",
        "brand": "Cadbury",
        "stock_quantity": 60,
        "cost_price": 140.0,
        "selling_price": 195.0,
        "weekly_sales_avg": 32,
        "expiry_days": 270,
        "customer_name": "Ananya Rao",
        "customer_phone": "+91 98459 66778",
        "customer_segment": "High Basket AOV VIP"
    },
    {
        "product_id": "SKU_SWT_06",
        "name": "Haldiram's Pure Desi Ghee Kaju Katli Silver Foil Box (500g)",
        "category": "Sweets & Confectionery",
        "brand": "Haldiram's",
        "stock_quantity": 40,
        "cost_price": 390.0,
        "selling_price": 550.0,
        "weekly_sales_avg": 18,
        "expiry_days": 45,
        "customer_name": "Priya Menon",
        "customer_phone": "+91 98459 22334",
        "customer_segment": "Festive Gifting & Dry Fruits"
    },
    # --- Coffee & Daily Beverage ---
    {
        "product_id": "SKU_BEV_05",
        "name": "Nescafe Classic 100% Pure Instant Coffee Glass Jar (100g)",
        "category": "Beverages",
        "brand": "Nescafe",
        "stock_quantity": 80,
        "cost_price": 235.0,
        "selling_price": 325.0,
        "weekly_sales_avg": 28,
        "expiry_days": 540,
        "customer_name": "Vikram Patel",
        "customer_phone": "+91 98459 77889",
        "customer_segment": "Coffee Connoisseurs"
    },
    # --- Household Cleaners ---
    {
        "product_id": "SKU_HGC_05",
        "name": "Lizol Disinfectant Surface & Floor Cleaner Citrus (2L)",
        "category": "Personal Care",
        "brand": "Lizol",
        "stock_quantity": 60,
        "cost_price": 310.0,
        "selling_price": 415.0,
        "weekly_sales_avg": 24,
        "expiry_days": 730,
        "customer_name": "Kavitha Shetty",
        "customer_phone": "+91 98459 44556",
        "customer_segment": "Home Hygiene & Essentials"
    },
    {
        "product_id": "SKU_HGC_06",
        "name": "Harpic Power Plus Original Disinfectant Toilet Cleaner (1L x 2)",
        "category": "Personal Care",
        "brand": "Harpic",
        "stock_quantity": 75,
        "cost_price": 280.0,
        "selling_price": 380.0,
        "weekly_sales_avg": 27,
        "expiry_days": 730,
        "customer_name": "Deepak Nair",
        "customer_phone": "+91 98459 11223",
        "customer_segment": "Home Hygiene & Essentials"
    }
]

df = pd.DataFrame(ITEMS)

# Output paths
os.makedirs("data", exist_ok=True)
csv_path_root = "retail_supermarket_inventory_test.csv"
xlsx_path_root = "retail_supermarket_inventory_test.xlsx"
csv_path_data = os.path.join("data", "retail_supermarket_inventory_test.csv")
xlsx_path_data = os.path.join("data", "retail_supermarket_inventory_test.xlsx")

# Save CSV
df.to_csv(csv_path_root, index=False, encoding="utf-8")
df.to_csv(csv_path_data, index=False, encoding="utf-8")

# Save Excel with formatting
with pd.ExcelWriter(xlsx_path_root, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Inventory_Catalog")

with pd.ExcelWriter(xlsx_path_data, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Inventory_Catalog")

print(f"Generated {len(df)} realistic retail SKU records!")
print(f"  CSV Root: {csv_path_root} ({os.path.getsize(csv_path_root)} bytes)")
print(f"  XLSX Root: {xlsx_path_root} ({os.path.getsize(xlsx_path_root)} bytes)")
print(f"  CSV Data: {csv_path_data} ({os.path.getsize(csv_path_data)} bytes)")
print(f"  XLSX Data: {xlsx_path_data} ({os.path.getsize(xlsx_path_data)} bytes)")
