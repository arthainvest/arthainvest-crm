// ==================== AUTO-LEAD ROUTING ENGINE ====================
// Automatically routes leads to sales reps based on intelligent criteria

class LeadRoutingEngine {
  constructor() {
    this.routingRules = {
      // Route by product type
      insurance: {
        priority: 1,
        preferredReps: ['Yogesh Khatri', 'Chirag Rathi'],
        skillSet: ['TATA', 'Niva Bupa', 'ICICI']
      },
      loans: {
        priority: 1,
        preferredReps: ['Amol Kasat', 'Employee 1'],
        skillSet: ['HDFC', 'ICICI', 'Axis']
      },
      mutualfunds: {
        priority: 2,
        preferredReps: ['Employee 2', 'Yogesh Khatri'],
        skillSet: ['Equity', 'Debt', 'Balanced']
      }
    };

    this.salesRepCapacity = {};
    this.repSpecializations = {};
  }

  /**
   * Main routing function - assigns lead to best-fit rep
   */
  routeLead(lead, availableReps) {
    const routingDecision = {
      leadId: lead.id,
      leadName: lead.name,
      score: 0,
      assignedRep: null,
      routingReason: [],
      alternativeReps: []
    };

    // Step 1: Determine product category
    const productType = this.detectProductType(lead);
    routingDecision.productType = productType;

    // Step 2: Calculate rep suitability scores
    const repScores = availableReps.map(rep => ({
      rep: rep.name,
      score: this.calculateRepScore(rep, lead, productType),
      capacity: this.getRepCapacity(rep.id),
      specialization: this.getRepSpecialization(rep.id, productType),
      recentClose: this.getRecentCloseRate(rep.id)
    }));

    // Step 3: Select best-fit rep
    const topRep = repScores.sort((a, b) => b.score - a.score)[0];

    if (topRep && topRep.score > 0) {
      routingDecision.assignedRep = topRep.rep;
      routingDecision.score = topRep.score;
      routingDecision.routingReason = [
        `Product Type: ${productType}`,
        `Rep Score: ${topRep.score}/100`,
        `Current Capacity: ${topRep.capacity}%`,
        `Specialization Match: ${topRep.specialization}`
      ];
      routingDecision.alternativeReps = repScores
        .slice(1, 3)
        .map(r => ({ name: r.rep, score: r.score }));
    }

    return routingDecision;
  }

  /**
   * Detect product type from lead data
   */
  detectProductType(lead) {
    const leadText = (
      lead.notes +
      lead.designation +
      lead.company
    ).toLowerCase();

    if (leadText.includes('insurance') || leadText.includes('policy')) {
      return 'insurance';
    } else if (leadText.includes('loan') || leadText.includes('credit')) {
      return 'loans';
    } else if (leadText.includes('fund') || leadText.includes('investment')) {
      return 'mutualfunds';
    }
    return 'general';
  }

  /**
   * Calculate suitability score for a rep
   */
  calculateRepScore(rep, lead, productType) {
    let score = 50; // Base score

    // Factor 1: Product specialization (30 points)
    const rules = this.routingRules[productType];
    if (rules) {
      if (rules.preferredReps.includes(rep.name)) {
        score += 30;
      } else {
        score += 15;
      }
    }

    // Factor 2: Current capacity (20 points)
    const capacity = this.getRepCapacity(rep.id);
    if (capacity < 60) {
      score += 20;
    } else if (capacity < 80) {
      score += 10;
    }

    // Factor 3: Recent performance (15 points)
    const closeRate = this.getRecentCloseRate(rep.id);
    if (closeRate > 0.3) {
      score += 15;
    } else if (closeRate > 0.2) {
      score += 10;
    }

    // Factor 4: Geographic proximity (15 points)
    if (lead.location && rep.location) {
      if (lead.location === rep.location) {
        score += 15;
      } else if (this.isSameRegion(lead.location, rep.location)) {
        score += 8;
      }
    }

    // Factor 5: Lead quality (20 points)
    const leadQuality = this.assessLeadQuality(lead);
    if (leadQuality === 'high') {
      score += 20; // Give high-quality leads to top performers
    } else if (leadQuality === 'medium') {
      score += 10;
    }

    return Math.min(score, 100);
  }

  /**
   * Get current workload of a sales rep
   */
  getRepCapacity(repId) {
    // Simulated capacity calculation
    // In production, query from database
    const capacity = this.salesRepCapacity[repId] || 50;
    return Math.min(capacity, 100);
  }

  /**
   * Get rep's specialization match for product type
   */
  getRepSpecialization(repId, productType) {
    const specs = this.repSpecializations[repId] || {};
    return specs[productType] || 'General';
  }

  /**
   * Calculate recent close rate for rep
   */
  getRecentCloseRate(repId) {
    // Simulated: Query last 30 days of deals
    // In production, calculate from database
    const closeRates = {
      'Yogesh Khatri': 0.35,
      'Chirag Rathi': 0.28,
      'Amol Kasat': 0.32,
      'Employee 1': 0.25,
      'Employee 2': 0.22
    };
    return closeRates[repId] || 0.2;
  }

  /**
   * Assess lead quality on scale: high, medium, low
   */
  assessLeadQuality(lead) {
    let quality = 'medium';

    const completeness = [
      lead.phone ? 1 : 0,
      lead.email ? 1 : 0,
      lead.company ? 1 : 0,
      lead.designation ? 1 : 0
    ].reduce((a, b) => a + b, 0);

    if (completeness >= 4) {
      quality = 'high';
    } else if (completeness <= 2) {
      quality = 'low';
    }

    return quality;
  }

  /**
   * Check if two locations are in same region
   */
  isSameRegion(loc1, loc2) {
    const regions = {
      'Mumbai': ['Bangalore', 'Pune'],
      'Delhi': ['Gurgaon', 'Noida'],
      'Bangalore': ['Hyderabad', 'Chennai']
    };

    return regions[loc1]?.includes(loc2) || regions[loc2]?.includes(loc1);
  }

  /**
   * Create routing rule
   */
  createRoutingRule(productType, config) {
    this.routingRules[productType] = config;
    return { success: true, message: `Routing rule created for ${productType}` };
  }

  /**
   * Update rep capacity
   */
  updateRepCapacity(repId, capacity) {
    this.salesRepCapacity[repId] = Math.max(0, Math.min(capacity, 100));
    return { success: true, capacity: this.salesRepCapacity[repId] };
  }

  /**
   * Get routing analytics
   */
  getRoutingAnalytics(timeframe = '30days') {
    return {
      timeframe,
      totalLeadsRouted: 245,
      averageRoutingAccuracy: 87,
      repUtilization: {
        'Yogesh Khatri': 78,
        'Chirag Rathi': 65,
        'Amol Kasat': 82,
        'Employee 1': 55,
        'Employee 2': 48
      },
      routingByType: {
        insurance: 120,
        loans: 85,
        mutualfunds: 40
      },
      conversionByRoutingQuality: {
        'high-quality-routing': 0.42,
        'medium-quality-routing': 0.28,
        'low-quality-routing': 0.15
      }
    };
  }
}

module.exports = LeadRoutingEngine;
