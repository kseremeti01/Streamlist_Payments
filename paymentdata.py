import pandas as pd
import plotly.express as px
import streamlit as st

# Hardcoded file path
file_path = r"C:\Users\username\Documents\PaymentData.csv"

# Load the dataset
ph_data = pd.read_csv(file_path, encoding='latin1')  # Adjust for encoding issues

# Ensure 'CreatedAt' column is in datetime format
ph_data['CreatedAt'] = pd.to_datetime(ph_data['CreatedAt'], errors='coerce', dayfirst=True)

# Create Date and Hour columns for easier filtering (without splitting 'CreatedAt')
ph_data['Date'] = pd.to_datetime(ph_data['CreatedAt'].dt.date)  # Ensure Date is in datetime format
ph_data['Hour'] = ph_data['CreatedAt'].dt.hour
ph_data['Time'] = ph_data['CreatedAt'].dt.time

# Sidebar Filters
st.sidebar.header("Filters")

# Brand Filter with 'All' option (changed to dropdown)
brands = ph_data['Brand'].unique()
brands = ['All'] + list(brands)  # Add 'All' option for the brands filter
selected_brand = st.sidebar.selectbox("Select Brand", brands, index=0)  # Default to 'All'

# Apply brand filter to update other filters
if selected_brand == 'All':
    filtered_data = ph_data
else:
    filtered_data = ph_data[ph_data['Brand'] == selected_brand]

# Set the title dynamically based on selected brand
st.title(f"Payment Data Q4 - {selected_brand if selected_brand != 'All' else 'All Brands'}")

# Update Date Range Filter based on selected Brand
min_date = filtered_data['Date'].min()
max_date = filtered_data['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Update Hour Filter based on selected Brand
hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))

# Update Amount Range Filter based on selected Brand
min_amount, max_amount = float(filtered_data['Amount'].min()), float(filtered_data['Amount'].max())
amount_range = st.sidebar.slider("Select Amount Range", min_amount, max_amount, (min_amount, max_amount))

# Update Carrier Filter dynamically based on selected Brand
carriers = ['All'] + list(filtered_data['Carrier'].unique())  # Add 'All' option for carriers
selected_carriers = st.sidebar.multiselect("Select Carriers", carriers, default=carriers)

# Update Service Filter dynamically based on selected Carriers
carrier_services_dict = {
    carrier: filtered_data[filtered_data['Carrier'] == carrier]['CarrierService'].unique()
    for carrier in selected_carriers if carrier != 'All'
}
selected_services = []
if selected_carriers != ['All']:  # Only show services if specific carriers are selected
    selected_services = st.sidebar.multiselect(
        "Select Services",
        options=[service for carrier in selected_carriers if carrier != 'All' for service in carrier_services_dict[carrier]],
        default=[service for carrier in selected_carriers if carrier != 'All' for service in carrier_services_dict[carrier]]
    )

# Apply final filter to the data
if selected_brand == 'All':
    filtered_data = filtered_data[
        (filtered_data['CarrierService'].isin(selected_services)) &
        (filtered_data['Date'].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))) &
        (filtered_data['Hour'].between(hour_range[0], hour_range[1])) &
        (filtered_data['Amount'].between(*amount_range))
    ]
else:
    filtered_data = filtered_data[
        (filtered_data['Carrier'].isin(selected_carriers)) &
        (filtered_data['CarrierService'].isin(selected_services)) &
        (filtered_data['Date'].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))) &
        (filtered_data['Hour'].between(hour_range[0], hour_range[1])) &
        (filtered_data['Amount'].between(*amount_range))
    ]

# Display filtered data preview
# st.write("Filtered Dataset Preview:")
# st.dataframe(filtered_data.head())

# Line Graph Across Time (counting rows instead of summing Amount)
st.header("Purchases across a period of time")
interval = st.selectbox(
    "Select time interval:",
    ["10T", "15T", "30T", "1H", "2H"],
    index=3  # Default to "1H"
)

if not filtered_data.empty:
    # Ensure 'CreatedAt' column exists in filtered_data for resampling
    resampled = filtered_data.set_index('CreatedAt').resample(interval).size()

    fig = px.line(resampled, x=resampled.index, y=resampled.values,
                  title=f"Number of Purchases Over Time ({interval})")
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Purchases"
    )
    st.plotly_chart(fig)
else:
    st.warning("No data available for the selected filters.")

# --- Start of the Second Graph: Average Purchases per 15-Min Interval ---
st.header("Average purchases during selected weekday")

# Allow the user to select a specific weekday
weekdays_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day = st.selectbox("Select day of the week:", weekdays_ordered)

# Filter data by the selected weekday (and the common date range filter)
filtered_day_data = filtered_data[filtered_data['Date'].dt.day_name() == day]

if not filtered_day_data.empty:
    # Group by 15-minute intervals and calculate average number of purchases
    filtered_day_data['TimeSlot'] = filtered_day_data['CreatedAt'].dt.floor('15T')
    avg_purchases = filtered_day_data.groupby(filtered_day_data['TimeSlot'].dt.time).size().reset_index(name='Average Purchases')

    # Create the line plot for average purchases per 15-minute time slot
    fig = px.line(avg_purchases, x='TimeSlot', y='Average Purchases',
                  title=f"Average Purchases on {day}s ({date_range[0]} to {date_range[1]})")

    # Reducing x-axis tick labels to avoid crowding by selecting a few time intervals
    tick_step = 2  # Step for displaying ticks (show every second time slot)

    fig.update_layout(
        xaxis_title="Time of Day (15-minute intervals)",
        yaxis_title="Average Purchases",
        xaxis=dict(
            tickformat="%H:%M",  # Format x-axis as time
            tickmode="array",
            tickvals=avg_purchases['TimeSlot'][::tick_step],  # Show every second time slot
            ticktext=avg_purchases['TimeSlot'][::tick_step].astype(str)  # Format the tick labels as time strings
        )
    )
    st.plotly_chart(fig)
else:
    st.warning(f"No data available for {day}s within the selected date range.")
