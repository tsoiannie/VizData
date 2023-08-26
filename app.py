from flask import Flask, render_template, request, jsonify
import requests
import plotly
import plotly.graph_objs as go

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/drug_chart")
def drug_chart():
    url = "https://api.fda.gov/drug/event.json"
    drug = request.args.get("drug", "Aspirin")
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug}"',
        "limit": 10,
        "skip": 0,
        "count": "patient.reaction.reactionmeddrapt.exact",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError("Failed to retrieve data: {}".format(response.content))

    data = response.json()

    if "results" not in data:
        raise ValueError("No results found in response: {}".format(data))

    reaction_names = [item["term"] for item in data["results"]]
    reaction_counts = [item["count"] for item in data["results"]]

    fig = go.Figure([go.Bar(x=reaction_counts, y=reaction_names, orientation="h")])

    fig.update_layout(
        title=f"Reactions Associated with {drug}", xaxis_title="Count", yaxis_title="Reaction"
    )

    chart_html = fig.to_html(full_html=False)

    return render_template("drug_chart.html", chart_html=chart_html)

@app.route("/drug_pie_chart")
def drug_pie_chart():
    url = "https://api.fda.gov/drug/event.json"

    drug = request.args.get("drug", "Aspirin")

    params = {
        "search": f'patient.drug.medicinalproduct:"{drug}"',
        "limit": 10,
        "skip": 0,
        "count": "patient.reaction.reactionmeddrapt.exact",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise ValueError("Failed to retrieve data: {}".format(response.content))

    data = response.json()

    if "results" not in data:
        raise ValueError("No results found in response: {}".format(data))

    reaction_names = [item["term"] for item in data["results"]]
    reaction_counts = [item["count"] for item in data["results"]]

    fig = go.Figure([go.Pie(labels=reaction_names, values=reaction_counts)])

    fig.update_layout(title=f"Reactions Associated with {drug}")

    chart_html = fig.to_html(full_html=False)

    return render_template(
        "drug_pie_chart.html", chart_html=chart_html, drugs=["Aspirin", "Ibuprofen", "Acetaminophen"]
    )

@app.route("/uk_holiday_bubble_chart")
def uk_holiday_bubble_chart():
    url = "https://www.gov.uk/bank-holidays.json"

    response = requests.get(url)
    data = response.json()

    holidays = {}
    for country, events in data.items():
        for event in events["events"]:
            year = event["date"].split("-")[0]
            if year not in holidays:
                holidays[year] = {}
            if country not in holidays[year]:
                holidays[year][country] = 0
            holidays[year][country] += 1

    fig = go.Figure()
    for country in holidays[list(holidays.keys())[0]].keys():
        fig.add_trace(
            go.Scatter(
                x=list(holidays.keys()),
                y=[holidays[year][country] for year in holidays],
                mode="markers",
                marker=dict(
                    size=[holidays[year][country] for year in holidays],
                    sizemode="diameter",
                    sizeref=0.1,
                    sizemin=5,
                ),
                name=country,
            )
        )

    fig.update_layout(
        title="Bank Holidays by Year and Country", xaxis_title="Year", yaxis_title="Count"
    )

    chart_html = fig.to_html(full_html=False)

    return chart_html

@app.route("/covid_dashboard", methods=["GET", "POST"])
def covid_dashboard():
    url = "https://disease.sh/v3/covid-19/historical/all?lastdays=all"

    response = requests.get(url)

    if response.status_code != 200:
        raise ValueError("Failed to retrieve data: {}".format(response.content))

    data = response.json()

    cases_data = data["cases"]
    deaths_data = data["deaths"]
    recoveries_data = data["recovered"]

    countries = list(cases_data.keys())

    country_data = {}

    for country in countries:
        if isinstance(cases_data[country], dict):
            total_cases = max(cases_data[country].values())
        else:
            total_cases = cases_data[country]
        if isinstance(deaths_data[country], dict):
            total_deaths = max(deaths_data[country].values())
        else:
            total_deaths = deaths_data[country]
        if isinstance(recoveries_data[country], dict):
            total_recoveries = max(recoveries_data[country].values())
        else:
            total_recoveries = recoveries_data[country]
        country_data[country] = {"cases": total_cases, "deaths": total_deaths, "recoveries": total_recoveries}

    sorted_country_data = sorted(
        country_data.items(), key=lambda x: x[1]["cases"], reverse=True
    )

    if request.method == "POST":
        search_query = request.form["search_query"]
        if search_query:
            sorted_country_data = [
                (country, data)
                for country, data in sorted_country_data
                if search_query.lower() in country.lower()
            ]

    table_html = '<table class="table table-striped"><thead><tr><th>Date</th><th>Total Cases</th><th>Total Deaths</th><th>Total Recoveries</th></tr></thead><tbody>'
    for country, data in sorted_country_data:
        table_html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            country, data["cases"], data["deaths"], data["recoveries"]
        )
    table_html += "</tbody></table>"

    cases = [data["cases"] for country, data in sorted_country_data]
    deaths = [data["deaths"] for country, data in sorted_country_data]
    recoveries = [data["recoveries"] for country, data in sorted_country_data]
    fig = go.Figure(
        data=[
            go.Bar(name="Cases", x=countries, y=cases),
            go.Bar(name="Deaths", x=countries, y=deaths),
            go.Bar(name="Recoveries", x=countries, y=recoveries),
        ]
    )
    fig.update_layout(
        title="Total COVID-19 Cases, Deaths, and Recoveries by Date",
        xaxis_title="Date",
        yaxis_title="Count",
    )

    chart_html = fig.to_html(full_html=False)

    return render_template(
        "dashboard.html",
        table_html=table_html,
        search_query=request.form.get("search_query", ""),
        chart_html=chart_html,
    )

if __name__ == "__main__":
    app.run(debug=True)