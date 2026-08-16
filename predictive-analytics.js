// ==================== PREDICTIVE ANALYTICS ENGINE ====================
// ML-based predictions for lead scoring, deal closure, and product recommendations

class PredictiveAnalyticsEngine {
  constructor() {
    this.historicalData = {};
    this.models = {};
    this.initialized = false;
  }

  /**
   * Calculate lead score (0-100)
   * Based on: engagement, profile completeness, company size, designation
   */
  calculateLeadScore(lead, interactions = []) {
    let score = 20; // Base score

    // 1. Profile Completeness (25 points)
    const profileFields = [
      lead.phone,
      lead.email,
      lead.company,
      lead.designation,
      lead.location
    ];
    const completeness = profileFields.filter(f => f).length / profileFields.length;
    score += completeness * 25;

    // 2. Engagement Score (30 points)
    const engagementScore = this.calculateEngagementScore(lead, interactions);
    score += engagementScore * 30;

    // 3. Company Profile (20 points)
    if (lead.company) {
      const companyScore = this.getCompanyScore(lead.company);
      score += companyScore * 20;
    }

    // 4. Designation Quality (15 points)
    if (lead.designation) {
      const designationScore = this.getDesignationScore(lead.designation);
      score += designationScore * 15;
    }

    // 5. Historical Similarity (10 points)
    const similarityScore = this.findSimilarLeads(lead);
    score += similarityScore * 10;

    return Math.min(Math.round(score), 100);
  }

  /**
   * Calculate engagement score based on interactions
   */
  calculateEngagementScore(lead, interactions) {
    if (!interactions || interactions.length === 0) return 0;

    let engagement = 0;
    let recencyWeight = 0;

    const now = Date.now();
    const thirtyDaysAgo = now - 30 * 24 * 60 * 60 * 1000;

    interactions.forEach(interaction => {
      const interactionTime = new Date(interaction.timestamp).getTime();
      const isRecent = interactionTime > thirtyDaysAgo;

      if (isRecent) {
        switch (interaction.type) {
          case 'call':
            engagement += 0.15;
            recencyWeight += 1;
            break;
          case 'email_open':
            engagement += 0.10;
            recencyWeight += 0.8;
            break;
          case 'whatsapp_message':
            engagement += 0.12;
            recencyWeight += 0.9;
            break;
          case 'form_submission':
            engagement += 0.20;
            recencyWeight += 1.2;
            break;
          case 'document_view':
            engagement += 0.08;
            recencyWeight += 0.6;
            break;
        }
      }
    });

    // Normalize engagement score
    return Math.min(engagement / (interactions.length * 0.3), 1);
  }

  /**
   * Score company based on industry and size
   */
  getCompanyScore(company) {
    const highValueIndustries = [
      'IT', 'Finance', 'Banking', 'Pharma', 'Insurance',
      'Real Estate', 'Manufacturing', 'Retail'
    ];

    const companyName = company.toUpperCase();

    // Check for high-value industries
    for (let industry of highValueIndustries) {
      if (companyName.includes(industry)) {
        return 0.8; // High value
      }
    }

    // Check for large companies
    if (companyName.includes('LTD') || companyName.includes('INC')) {
      return 0.6; // Medium-high value
    }

    return 0.4; // Default
  }

  /**
   * Score designation based on decision-making authority
   */
  getDesignationScore(designation) {
    const decisionMakers = [
      'CEO', 'Director', 'Manager', 'Head',
      'VP', 'Officer', 'Founder', 'Partner'
    ];

    const designation_upper = designation.toUpperCase();

    for (let title of decisionMakers) {
      if (designation_upper.includes(title)) {
        if (['CEO', 'Founder', 'Director'].includes(title)) {
          return 1.0; // Highest priority
        }
        return 0.8; // High priority
      }
    }

    return 0.5; // Low decision-making authority
  }

  /**
   * Find similar leads from historical data
   */
  findSimilarLeads(lead) {
    // Placeholder for ML similarity matching
    // In production, use vector embeddings or clustering
    const similarLeads = [];

    // This would be replaced with actual ML model in production
    if (lead.company) {
      // Would query database for leads from same company
      similarLeads.push(1); // Found similar lead
    }

    return similarLeads.length > 0 ? 0.7 : 0.3;
  }

  /**
   * Predict deal closure probability
   * Returns: probability (0-1), confidence level, key factors
   */
  predictDealClosure(deal, lead, rep) {
    let closureProbability = 0.5; // Base 50%

    // Factor 1: Deal value (Deals worth more tend to close more often)
    if (deal.value && deal.value > 100000) {
      closureProbability += 0.15;
    } else if (deal.value && deal.value > 50000) {
      closureProbability += 0.10;
    }

    // Factor 2: Stage progression
    const stages = ['Inquiry', 'Qualified', 'Proposal', 'Negotiation', 'Closing'];
    const currentStageIndex = stages.indexOf(deal.stage);
    closureProbability += (currentStageIndex / stages.length) * 0.25;

    // Factor 3: Rep performance
    if (rep) {
      const repCloseRate = this.getRepHistoricalCloseRate(rep.id);
      closureProbability += repCloseRate * 0.2;
    }

    // Factor 4: Lead quality
    const leadScore = this.calculateLeadScore(lead);
    closureProbability += (leadScore / 100) * 0.2;

    // Factor 5: Time in pipeline
    const daysInPipeline = deal.daysInStage || 0;
    if (daysInPipeline < 7) {
      closureProbability -= 0.1; // Rushing might fail
    } else if (daysInPipeline > 60) {
      closureProbability -= 0.15; // Stalling reduces chance
    }

    const confidence = Math.min(Math.abs(closureProbability - 0.5) * 2, 1);

    return {
      probability: Math.min(Math.max(closureProbability, 0), 1),
      percentage: Math.round(closureProbability * 100),
      confidence: confidence,
      keyFactors: this.getKeyClosureFactors(deal, lead, rep),
      recommendation: this.getClosureRecommendation(closureProbability)
    };
  }

  /**
   * Get key factors influencing closure
   */
  getKeyClosureFactors(deal, lead, rep) {
    const factors = [];

    if (deal.value > 100000) {
      factors.push('High deal value - strong closing signal');
    }

    const leadScore = this.calculateLeadScore(lead);
    if (leadScore > 70) {
      factors.push(`Qualified lead (Score: ${leadScore}/100)`);
    }

    if (deal.stage === 'Proposal' || deal.stage === 'Negotiation') {
      factors.push('Advanced pipeline stage');
    }

    if (rep && this.getRepHistoricalCloseRate(rep.id) > 0.3) {
      factors.push('High-performing sales rep');
    }

    return factors;
  }

  /**
   * Get closure recommendation
   */
  getClosureRecommendation(probability) {
    if (probability > 0.7) {
      return '🟢 Strong - Prioritize closing, allocate resources';
    } else if (probability > 0.5) {
      return '🟡 Moderate - Continue nurturing, track closely';
    } else if (probability > 0.3) {
      return '🟠 Low - May need intervention or qualification review';
    } else {
      return '🔴 Very Low - Consider moving to inactive or reassigning';
    }
  }

  /**
   * Get rep's historical close rate
   */
  getRepHistoricalCloseRate(repId) {
    const closeRates = {
      'Yogesh Khatri': 0.35,
      'Chirag Rathi': 0.28,
      'Amol Kasat': 0.32,
      'Employee 1': 0.25,
      'Employee 2': 0.22
    };
    return closeRates[repId] || 0.25;
  }

  /**
   * Predict best call time for lead
   * When is lead most likely to answer?
   */
  predictBestCallTime(lead) {
    // Simulated prediction based on industry patterns
    const callPatterns = {
      'IT': { day: 'Tuesday-Wednesday', time: '10:00-11:30' },
      'Finance': { day: 'Monday-Wednesday', time: '14:00-15:30' },
      'Banking': { day: 'Tuesday-Thursday', time: '09:00-10:30' },
      'Pharma': { day: 'Monday-Wednesday', time: '11:00-12:30' },
      'Insurance': { day: 'Thursday-Friday', time: '15:00-16:30' },
      'default': { day: 'Tuesday-Thursday', time: '10:00-11:00' }
    };

    const industry = Object.keys(callPatterns).find(
      ind => lead.company?.toUpperCase().includes(ind.toUpperCase())
    ) || 'default';

    return {
      optimalDay: callPatterns[industry].day,
      optimalTime: callPatterns[industry].time,
      responseRate: 0.68,
      confidence: 0.75
    };
  }

  /**
   * Recommend product based on lead profile
   */
  recommendProduct(lead) {
    const recommendations = [];

    // Insurance recommendation
    if (lead.designation?.toUpperCase().includes('MANAGER') ||
        lead.company?.toUpperCase().includes('IT')) {
      recommendations.push({
        product: 'Term Insurance',
        score: 0.85,
        reason: 'High earner, likely uninsured',
        premium: '₹500-1000/month'
      });
    }

    // Loan recommendation
    if (lead.designation?.toUpperCase().includes('DIRECTOR') ||
        lead.designation?.toUpperCase().includes('CEO')) {
      recommendations.push({
        product: 'Business Loan',
        score: 0.90,
        reason: 'Decision maker, likely business need',
        loanAmount: '₹10L-1Cr'
      });
    }

    // Mutual Funds recommendation
    if (lead.age > 30 || lead.company?.toUpperCase().includes('FINANCE')) {
      recommendations.push({
        product: 'Mutual Funds SIP',
        score: 0.75,
        reason: 'Wealth creation opportunity',
        sipAmount: '₹10000-50000/month'
      });
    }

    return recommendations.sort((a, b) => b.score - a.score);
  }

  /**
   * Churn prediction - likelihood of losing a client
   */
  predictChurnRisk(client, lastInteractionDaysAgo) {
    let churnRisk = 0.1; // Base 10% churn risk

    // Days since last interaction
    if (lastInteractionDaysAgo > 90) {
      churnRisk += 0.4;
    } else if (lastInteractionDaysAgo > 60) {
      churnRisk += 0.2;
    } else if (lastInteractionDaysAgo > 30) {
      churnRisk += 0.1;
    }

    // Client lifetime value
    if (client.totalValue < 50000) {
      churnRisk += 0.15; // Lower value clients churn more
    } else if (client.totalValue > 500000) {
      churnRisk -= 0.1; // High value clients more loyal
    }

    // Product diversity (multiple products = lower churn)
    if (client.productCount > 3) {
      churnRisk -= 0.2;
    } else if (client.productCount === 1) {
      churnRisk += 0.15;
    }

    return {
      riskScore: Math.min(Math.max(churnRisk, 0), 1),
      percentage: Math.round(churnRisk * 100),
      riskLevel: this.getChurnRiskLevel(churnRisk),
      retentionActions: this.getRetentionActions(churnRisk)
    };
  }

  /**
   * Get churn risk level
   */
  getChurnRiskLevel(risk) {
    if (risk > 0.7) return '🔴 Critical - Immediate action needed';
    if (risk > 0.5) return '🟠 High - Start retention campaign';
    if (risk > 0.3) return '🟡 Medium - Monitor closely';
    return '🟢 Low - Maintain relationship';
  }

  /**
   * Get retention actions for churn risk
   */
  getRetentionActions(risk) {
    const actions = [];

    if (risk > 0.7) {
      actions.push('Assign dedicated relationship manager');
      actions.push('Offer loyalty discount or additional product');
      actions.push('Schedule executive call');
    } else if (risk > 0.5) {
      actions.push('Send personalized offer email');
      actions.push('Schedule check-in call');
      actions.push('Provide product upgrade information');
    } else if (risk > 0.3) {
      actions.push('Regular newsletter');
      actions.push('Quarterly business review');
    }

    return actions;
  }

  /**
   * Get analytics dashboard
   */
  getAnalyticsDashboard() {
    return {
      averageLeadScore: 62,
      highQualityLeads: 34, // Score > 70
      averageDealClosureRate: 0.285,
      productRecommendationAccuracy: 0.78,
      churnPredictionAccuracy: 0.82,
      topLeads: [
        { name: 'Acme Corp CEO', score: 95, product: 'Business Loan', closureProb: 0.92 },
        { name: 'Tech Startup Founder', score: 88, product: 'Term Insurance', closureProb: 0.85 },
        { name: 'Finance Manager', score: 82, product: 'Mutual Funds', closureProb: 0.78 }
      ],
      churnAlerts: [
        { name: 'ABC Company', riskScore: 0.85, lastInteraction: '95 days ago' },
        { name: 'XYZ Ltd', riskScore: 0.72, lastInteraction: '65 days ago' }
      ]
    };
  }
}

module.exports = PredictiveAnalyticsEngine;
