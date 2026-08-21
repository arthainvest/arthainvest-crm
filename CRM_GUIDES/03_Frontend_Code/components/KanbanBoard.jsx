import React, { useState, useEffect } from 'react';
import { getDeals, moveDeal, getLeads } from '../services/api';
import '../styles/KanbanBoard.css';

export default function KanbanBoard() {
  const [deals, setDeals] = useState([]);
  const [leads, setLeads] = useState({});
  const [loading, setLoading] = useState(true);
  const [draggedDeal, setDraggedDeal] = useState(null);
  const token = localStorage.getItem('token');

  const stages = ['new', 'qualified', 'proposal', 'negotiation', 'closed'];
  const stageLabels = {
    new: 'New',
    qualified: 'Qualified',
    proposal: 'Proposal',
    negotiation: 'Negotiation',
    closed: 'Closed',
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [dealsData, leadsData] = await Promise.all([
        getDeals(token),
        getLeads(token),
      ]);

      setDeals(dealsData);

      const leadsMap = {};
      leadsData.forEach((lead) => {
        leadsMap[lead.id] = lead;
      });
      setLeads(leadsMap);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (deal) => {
    setDraggedDeal(deal);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (stage) => {
    if (!draggedDeal) return;

    try {
      await moveDeal(token, draggedDeal.id, stage);
      setDraggedDeal(null);
      fetchData();
    } catch (err) {
      console.error('Failed to move deal:', err);
      alert('Error moving deal');
    }
  };

  if (loading) {
    return <div className="kanban-container"><p>Loading...</p></div>;
  }

  return (
    <div className="kanban-container">
      <h1>Pipeline</h1>

      <div className="kanban-board">
        {stages.map((stage) => (
          <div
            key={stage}
            className="kanban-column"
            onDragOver={handleDragOver}
            onDrop={() => handleDrop(stage)}
          >
            <div className="column-header">
              <h2>{stageLabels[stage]}</h2>
              <span className="deal-count">
                {deals.filter((d) => d.stage === stage).length}
              </span>
            </div>

            <div className="column-body">
              {deals
                .filter((deal) => deal.stage === stage)
                .map((deal) => (
                  <DealCard
                    key={deal.id}
                    deal={deal}
                    lead={leads[deal.lead_id]}
                    onDragStart={handleDragStart}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DealCard({ deal, lead, onDragStart }) {
  return (
    <div
      className="deal-card"
      draggable
      onDragStart={() => onDragStart(deal)}
    >
      <div className="deal-header">
        <h3>{lead?.name || `Lead #${deal.lead_id}`}</h3>
        <span className="deal-value">₹{deal.deal_value?.toLocaleString() || '0'}</span>
      </div>

      <div className="deal-body">
        <p className="company">{lead?.company || 'No company'}</p>
        <p className="tier">
          Tier: <strong>{lead?.lead_tier || 'N/A'}</strong>
        </p>
      </div>

      <div className="deal-footer">
        <span className="probability">
          {(deal.probability * 100).toFixed(0)}% prob.
        </span>
      </div>
    </div>
  );
}
