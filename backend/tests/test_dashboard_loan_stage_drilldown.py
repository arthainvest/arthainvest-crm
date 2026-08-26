LOAN_STAGE_LABELS = ["Deals Closed (This Month)", "In Progress", "Rejected", "On Hold", "Login/Sanction", "Disbursed"]


def test_loan_stage_deals_matches_aggregate_for_every_bucket(auth_client):
    """The Dashboard's Loan Pipeline cards show a count/value per bucket - the drill-down must
    match both exactly, for every bucket, or the numbers on the card would contradict what
    clicking into it shows. Both are computed from the same _loan_stage_where clause."""
    analytics = auth_client.get("/api/analytics/dashboard").json()
    buckets = {b["label"]: b for b in analytics["loan_stages"]}

    for label in LOAN_STAGE_LABELS:
        bucket = buckets[label]
        resp = auth_client.get(f"/api/analytics/dashboard/loan-stage-deals?label={label}")
        assert resp.status_code == 200
        deals = resp.json()
        assert len(deals) == bucket["count"], f"count mismatch for {label}"
        assert sum(d["deal_value"] for d in deals) == bucket["value"], f"value mismatch for {label}"


def test_loan_stage_deals_unknown_label_404s(auth_client):
    resp = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=Not+A+Real+Bucket")
    assert resp.status_code == 404


def test_moving_a_deal_to_closed_updates_in_progress_and_this_month_buckets(auth_client):
    deal = auth_client.get("/api/deals").json()[0]

    before_in_progress = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=In Progress").json()
    assert deal["id"] in {d["id"] for d in before_in_progress}

    auth_client.put(f"/api/deals/{deal['id']}/move", json={"stage": "closed"})

    after_in_progress = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=In Progress").json()
    assert deal["id"] not in {d["id"] for d in after_in_progress}

    this_month = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=Deals Closed (This Month)").json()
    assert deal["id"] in {d["id"] for d in this_month}

    analytics = auth_client.get("/api/analytics/dashboard").json()
    buckets = {b["label"]: b for b in analytics["loan_stages"]}
    assert buckets["In Progress"]["count"] == len(after_in_progress)
    assert buckets["Deals Closed (This Month)"]["count"] == len(this_month)


def test_login_sanction_bucket_reflects_process_status_change(auth_client):
    """Seeded deals default to process_status='Login', which falls in the Login/Sanction
    bucket - moving one to Disbursed must move it out of one drill-down and into the other."""
    deal = auth_client.get("/api/deals").json()[1]
    login_before = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=Login/Sanction").json()
    assert deal["id"] in {d["id"] for d in login_before}

    auth_client.put(f"/api/deals/{deal['id']}/process-status", json={"process_status": "Disbursed"})

    login_after = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=Login/Sanction").json()
    disbursed = auth_client.get("/api/analytics/dashboard/loan-stage-deals?label=Disbursed").json()
    assert deal["id"] not in {d["id"] for d in login_after}
    assert deal["id"] in {d["id"] for d in disbursed}
