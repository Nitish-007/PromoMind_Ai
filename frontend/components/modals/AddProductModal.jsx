"use client";

import React, { useState } from "react";
import { Plus, X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CustomSelect } from "@/components/ui/custom-select";

const CATEGORIES = [
  "Staples & Oils",
  "Dairy",
  "Beverages",
  "Snacks",
  "Dry Fruits",
  "Puja & Festive",
  "Personal Care",
];

export function AddProductModal({ isOpen, onClose, onAddProduct }) {
  const [formData, setFormData] = useState({
    name: "",
    category: "Staples & Oils",
    stock_quantity: 50,
    cost_price: 180,
    selling_price: 230,
    weekly_sales_avg: 25,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name) return;
    setIsSubmitting(true);
    try {
      await onAddProduct({
        ...formData,
        stock_quantity: parseInt(formData.stock_quantity),
        cost_price: parseFloat(formData.cost_price),
        selling_price: parseFloat(formData.selling_price),
        weekly_sales_avg: parseInt(formData.weekly_sales_avg),
      });
      onClose();
    } catch (err) {
      console.error("Failed to add SKU:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="relative w-full max-w-md rounded-2xl border bg-card shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Plus className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-base text-foreground">Add Retail SKU</h3>
              <p className="text-xs text-muted-foreground">Runs open-source Holt&apos;s demand forecasting</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Product Name & Variant:</label>
            <Input
              type="text"
              placeholder="e.g. Aashirvaad Shudh Chakki Atta (5kg)"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Category:</label>
              <CustomSelect
                value={formData.category}
                onChange={(val) => setFormData({ ...formData, category: val })}
                options={CATEGORIES}
                placeholder="Select category..."
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Stock Quantity:</label>
              <Input
                type="number"
                min="1"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value })}
                required
                className="text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Retailer Cost Price (₹):</label>
              <Input
                type="number"
                step="0.5"
                value={formData.cost_price}
                onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                required
                className="text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Selling MRP (₹):</label>
              <Input
                type="number"
                step="0.5"
                value={formData.selling_price}
                onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                required
                className="text-xs"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Avg Weekly Sales (Units):</label>
            <Input
              type="number"
              min="1"
              value={formData.weekly_sales_avg}
              onChange={(e) => setFormData({ ...formData, weekly_sales_avg: e.target.value })}
              required
              className="text-xs"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t">
            <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={isSubmitting} className="text-xs gap-1.5">
              {isSubmitting ? (
                <span>Adding SKU...</span>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Add SKU & Forecast</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

