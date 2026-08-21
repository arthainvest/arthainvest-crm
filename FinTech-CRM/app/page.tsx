'use client';

import React from 'react';
import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/10 backdrop-blur-md border-b border-white/10 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg"></div>
              <span className="text-xl font-bold text-white">ArthaInvest CRM</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-300 hover:text-white transition">Features</a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition">Pricing</a>
              <div className="flex space-x-4">
                <Link
                  href="/login"
                  className="px-6 py-2 text-white hover:bg-white/10 rounded-lg transition"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/50 transition"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Professional Fintech CRM for
              <span className="bg-gradient-to-r from-cyan-500 to-blue-600 bg-clip-text text-transparent">
                {' '}Financial Distribution
              </span>
            </h1>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Complete CRM solution built for financial advisors and distributors. Manage contacts, pipelines, calls, and revenue with industry-leading features.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/signup"
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/50 transition font-semibold"
              >
                Start Free Trial
              </Link>
              <Link
                href="#features"
                className="px-8 py-3 bg-white/10 text-white rounded-lg hover:bg-white/20 transition font-semibold border border-white/20"
              >
                Learn More
              </Link>
            </div>
          </motion.div>

          {/* Feature Grid */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            id="features"
            className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            {[
              {
                icon: '📊',
                title: 'Advanced Dashboard',
                description: 'Real-time KPIs, funnel analytics, and revenue forecasting'
              },
              {
                icon: '📞',
                title: 'Click-to-Call',
                description: 'One-click calling with automatic logging and follow-ups'
              },
              {
                icon: '💬',
                title: 'Multi-Channel',
                description: 'WhatsApp, Email, SMS, and Call management in one place'
              },
              {
                icon: '🤖',
                title: 'AI-Powered',
                description: 'Voice transcription and AI status updates from calls'
              },
              {
                icon: '📈',
                title: 'Pipeline Management',
                description: 'Customizable pipelines for different sales stages'
              },
              {
                icon: '👥',
                title: 'Lead Distribution',
                description: 'Auto-assign and track leads by location and criteria'
              },
              {
                icon: '📄',
                title: 'Import/Export',
                description: 'Bulk import CSV/Excel, export to PDF/Excel'
              },
              {
                icon: '🔐',
                title: 'DigiLocker',
                description: 'Secure document management and verification'
              },
              {
                icon: '📱',
                title: 'Mobile App',
                description: 'Full CRM access on mobile with offline support'
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                className="bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 hover:bg-white/10 transition"
              >
                <div className="text-3xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-white/5 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center text-gray-400">
            <p>© 2026 ArthaInvest. Built with care for financial advisors.</p>
            <p className="text-sm mt-2">Production-Grade Fintech CRM combining Kylas design with advanced features</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
