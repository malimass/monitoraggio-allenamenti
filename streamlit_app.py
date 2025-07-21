import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Titolo app
st.title("Monitoraggio Allenamenti Massimo Malivindi")

# Dati allenamenti
raw_data = [
    ["31-12-2024", 16.93, 116, 1276],
    ["28-05-2025", 0.0, 106, 976],
    ["30-05-2025", 0.0, 110, 364],
    ["01-06-2025", 0.0, 113, 383],
    ["04-06-2025", 0.0, 112, 368],
    ["20-06-2025", 9.14, 124, 1479],
    ["22-06-2025", 9.14, 137, 1130],
    ["23-06-2025", 18.08, 115, 2010],
    ["25-06-2025", 7.76, 125, 827],
    ["27-06-2025", 10.31, 115, 940],
    ["02-07-2025", 19.02, 122, 1291],
    ["04-07-2025", 7.16, 118, 658],
    ["06-07-2025", 11.88, 114, 1509],
    ["08-07-2025", 18.79, 112, 1686],
    ["10-07-2025", 7.18, 112, 750],
    ["11-07-2025", 8.41, 118, 814],
    ["13-07-2025", 20.04, 112, 2320],
    ["15-07-2025", 18.39, 90, 1552],
    ["17-07-2025", 12.34, 103, 1016],
    ["20-07-2025", 22.69, 122, 2668],
    ["21-07-2025", 7.54, 110, 722]
]

# Crea DataFrame
columns = ["Data", "Distanza (km)", "FC media", "Calorie"]
df = pd.DataFrame(raw_data, columns=columns)
df["Data"] = pd.to_datetime(df["Data"], format="%d-%m-%Y")
df = df.sort_values("Data")

# Mostra tabella
st.subheader("Tabella riepilogativa")
st.dataframe(df)

# Grafico Distanza
st.subheader("Andamento della Distanza Percorsa")
fig1, ax1 = plt.subplots()
ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
ax1.set_ylabel("Distanza (km)")
ax1.set_xlabel("Data")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig1)

# Grafico Frequenza Cardiaca
st.subheader("Andamento della Frequenza Cardiaca Media")
fig2, ax2 = plt.subplots()
ax2.plot(df["Data"], df["FC media"], color='orange', marker='x')
ax2.set_ylabel("Frequenza Cardiaca Media (bpm)")
ax2.set_xlabel("Data")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig2)

# Grafico Calorie
st.subheader("Andamento Calorie Bruciate")
fig3, ax3 = plt.subplots()
ax3.bar(df["Data"], df["Calorie"], color='green')
ax3.set_ylabel("Calorie")
ax3.set_xlabel("Data")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig3)
