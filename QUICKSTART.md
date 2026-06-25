# Quick Start Guide - IITB Ambulance Service

## 🚀 Quick Setup (5 minutes)

### Step 1: Get API Key (2 minutes)
1. Go to: https://openrouteservice.org/dev/#/signup
2. Sign up with your email
3. Verify your email
4. Copy your API key from the dashboard

### Step 2: Configure API Key (1 minute)
Open `config.py` and replace `YOUR_API_KEY_HERE` with your actual API key:
```python
ORS_API_KEY = 'your_actual_api_key_here'
```

### Step 3: Run Setup (1 minute)
```bash
python setup.py
```

### Step 4: Start Application (1 minute)
```bash
python app.py
```

### Step 5: Open Browser
Navigate to: http://localhost:5000

## 📝 First Trip

1. **Form will auto-fill:**
   - Date: Current date
   - Time: Current time
   - KM Reading: Starting odometer value

2. **Fill in:**
   - Select pickup location (e.g., "Hostel 5 (Vikings)")
   - Patient name (e.g., "User1")
   - Driver name (e.g., "Driver1")
   - Purpose (e.g., "pickup")
   - Notes (optional)

3. **Click "Submit Trip"**

4. **Watch the magic:**
   - Route Map: See animated ambulance travel from hospital → pickup → hospital
   - Trip Summary: View distance, duration, and updated odometer
   - Analysis Map: See isochrone zones and route patterns

5. **Export Data:**
   - Click "Export CSV" to download all trip data

## 🎨 UI Features

- **Dark Theme**: Premium dark mode with gradients
- **Animated Route**: Watch ambulance move along the route
- **Real-time Updates**: Odometer updates automatically
- **Dual Maps**: Route visualization + Analytics
- **Responsive**: Works on desktop, tablet, and mobile

## 🗺️ Analysis Features

### Isochrone Zones
- **Green**: 3-minute reachable area
- **Yellow**: 5-minute reachable area
- **Red**: 7-minute reachable area

### Route Frequency
- **Red lines**: Most frequently used routes
- **Orange lines**: Moderately used routes
- **Yellow lines**: Less frequently used routes

## 🔧 Troubleshooting

### "API Key Error"
- Make sure you've added your API key to `config.py`
- Check if the key is valid at openrouteservice.org

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Database error"
```bash
python setup.py
```

## 📊 Sample Data

After a few trips, you'll see:
- Route patterns emerge on the analysis map
- Frequently used routes highlighted in red
- Isochrone zones showing hospital coverage

## 🎯 Next Steps

1. Record multiple trips to see route frequency analysis
2. Export CSV for external analysis
3. Customize campus locations in `config.py`
4. Adjust isochrone times in `app.py` (currently 3, 5, 7 min)

---

**Need Help?** Check README.md for detailed documentation.
