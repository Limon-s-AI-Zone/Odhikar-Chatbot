import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, AlertTriangle, AlertCircle, PhoneCall, 
  CheckCircle2, ChevronRight, RefreshCw, ArrowRightCircle,
  MessageSquare, User, Bot, WifiOff, KeyRound, AlertOctagon, XCircle,
  Volume2, VolumeX, FileText, Mic, Square, Radio,
  Shield, Trash2, Copy, Check, Sparkles, Scale, HeartHandshake, MapPin,
  ChevronDown, ChevronUp, Edit3, Download, Printer, Loader2
} from 'lucide-react';
import { downloadDraftPdf, printDraftPdf } from './utils/draftPdfGenerator';

interface IntakeProps {
  onCaseSubmitted: () => void;
}

interface ChatMessage {
  role: string;
  content: string;
  failed?: boolean;
}

export interface LlmErrorInfo {
  title: string;
  message: string;
  code?: string | number;
  details?: string;
  errorType?: string;
  troubleshooting?: string[];
}

export interface HelperChip {
  label: string;
  text: string;
}

export function getContextualChips(
  question: string | null,
  backendReplies?: string[],
  category?: string
): HelperChip[] {
  // 1. If backend provided customized replies from LLM or pipeline, format and present them
  if (backendReplies && backendReplies.length > 0) {
    return backendReplies.map((reply) => {
      let label = reply;
      if (reply.length > 20) {
        if (reply.includes('বাবার বাড়ি')) label = 'বাবার বাড়িতে আছে';
        else if (reply.includes('স্বামীর কাছে')) label = 'স্বামীর কাছে আছে';
        else if (reply.includes('কাজী অফিস')) label = 'কাজী অফিসের তথ্য আছে';
        else if (reply.includes('কাগজ নেই') || reply.includes('দলিল নেই')) label = 'কোনো কাগজ নেই';
        else if (reply.includes('১ লাখ')) label = '১ লাখ টাকা';
        else if (reply.includes('২ লাখ')) label = '২ লাখ টাকা';
        else if (reply.includes('৫ লাখ')) label = '৫ লাখ টাকা';
        else if (reply.includes('৫০ হাজার')) label = '৫০ হাজার - ১ লাখ';
        else if (reply.includes('হাজিরা') || reply.includes('স্লিপ')) label = 'হাজিরা খাতা/স্লিপ আছে';
        else if (reply.includes('মালিকের নাম')) label = 'মালিকের তথ্য আছে';
        else if (reply.includes('সাক্ষী আছেন') || reply.includes('প্রত্যক্ষদর্শী')) label = 'সাক্ষী আছেন';
        else if (reply.includes('কোনো সাক্ষী নেই') || reply.includes('কাজী বা সাক্ষী নেই')) label = 'কোনো সাক্ষী নেই';
        else if (reply.includes('পরিবার') || reply.includes('আত্মীয়')) label = 'পরিবার জানে';
        else if (reply.includes('মুরব্বি')) label = 'মুরব্বিরা জানেন';
        else if (reply.includes('মৌখিক')) label = 'মৌখিক চুক্তি ছিল';
        else if (reply.includes('১ মাস')) label = '১ মাস কাজ করেছি';
        else if (reply.includes('৬ মাস')) label = '৬ মাস কাজ করেছি';
        else if (reply.includes('১ বছর')) label = '১ বছরের বেশি';
        else if (reply.includes('১টি সন্তান')) label = '১টি সন্তান আছে';
        else if (reply.includes('২টি সন্তান')) label = '২টি সন্তান আছে';
        else if (reply.includes('আমাদের দখলেই')) label = 'আমাদের দখলে আছে';
        else if (reply.includes('প্রতিপক্ষ জোরপূর্বক') || reply.includes('অবৈধভাবে দখল')) label = 'প্রতিপক্ষ দখল করেছে';
        else if (reply.includes('ওয়ারিশ ও অংশ')) label = 'পৈতৃক ওয়ারিশ বিরোধ';
        else if (reply.includes('সীমানা নির্ধারণ') || reply.includes('সীমানা নিয়ে')) label = 'সীমানা নিয়ে বিরোধ';
        else if (reply.includes('মূল দলিল') || reply.includes('রেজিস্ট্রি দলিল')) label = 'মূল দলিল আছে';
        else if (reply.includes('খতিয়ান') || reply.includes('পর্চা')) label = 'খতিয়ান/পর্চা আছে';
        else if (reply.includes('প্রতিপক্ষের দখলে আটকে')) label = 'দলিল প্রতিপক্ষের কাছে';
        else if (reply.includes('কোনো বৈধ দলিল')) label = 'কোনো কাগজ নেই';
        else if (reply.includes('দখলে')) label = 'জমি দখলে আছে';
        else if (reply.includes('দাখিলা') || reply.includes('রশিদ')) label = 'দাখিলা/রশিদ আছে';
        else if (reply.includes('মেম্বার বা চেয়ারম্যান') || reply.includes('চেয়ারম্যানের কাছে সালিশ')) label = 'মেম্বার/চেয়ারম্যানের সালিশ';
        else if (reply.includes('পারিবারিক শরিক')) label = 'শরিকদের সাথে বিরোধ';
        else if (reply.includes('বাইরের প্রভাবশালী')) label = 'বাইরের দখলদার';
        else if (reply.includes('কোনো সালিশ বা মীমাংসার বৈঠক হয়নি') || reply.includes('কোনো সালিশ হয়নি')) label = 'কোনো সালিশ হয়নি';
        else if (reply.includes('সালিশ')) label = 'সালিশ হয়েছিল';
        else if (reply.includes('জিডি')) label = 'থানায় জিডি করেছি';
        else if (reply.includes('যৌতুকের দাবি')) label = 'যৌতুকের দাবি';
        else if (reply.includes('দ্বিতীয় বিয়ে') || reply.includes('দ্বিতীয় বিয়ে')) label = 'দ্বিতীয় বিয়ে করেছে';
        else if (reply.includes('বনিবনা না হওয়ায়')) label = 'বনিবনা হয়নি';
        else if (reply.includes('তাড়িয়ে দিয়েছে')) label = 'তাড়িয়ে দিয়েছে';
        else if (reply.includes('জাল দলিল')) label = 'জাল দলিল তৈরি';
        else if (reply.includes('সীমানা কেটে')) label = 'সীমানা কেটে দখল';
        else if (reply.includes('ছাঁটাই')) label = 'কাজ থেকে ছাঁটাই';
        else if (reply.includes('নির্দিষ্ট মনে নেই') || reply.includes('মনে করা যাচ্ছে না')) label = 'নির্দিষ্ট মনে নেই';
        else if (reply.includes('কারও কাছেই তথ্য নেই')) label = 'কারও তথ্য নেই';
        else label = reply.slice(0, 18) + '...';
      }
      return { label, text: reply };
    });
  }

  const q = (question || '').toLowerCase();
  const cat = (category || '').toLowerCase();

  // 0. Cause of dispute / why maintenance problem occurred ("ভরণপোষণ নিয়ে ঝামেলা হয়েছে কেন?")
  if (
    (q.includes('ঝামেলা') || q.includes('কারণ') || q.includes('কেন') || q.includes('সূত্রপাত')) && 
    (q.includes('ভরণপোষণ') || cat.includes('family') || cat.includes('dower'))
  ) {
    return [
      { label: 'যৌতুকের দাবিতে', text: 'যৌতুকের দাবিতে ঝগড়া করে খরচ দেওয়া বন্ধ করেছে' },
      { label: 'দ্বিতীয় বিয়ে করেছে', text: 'স্বামী দ্বিতীয় বিয়ে করে আমাদের ছেড়ে চলে গেছে' },
      { label: 'বনিবনা না হওয়ায়', text: 'শ্বশুরবাড়ির অত্যাচার ও বনিবনা না হওয়ায় আলাদা হয়ে গেছে' },
      { label: 'তাড়িয়ে দিয়েছে', text: 'বিনা কারণে হঠাৎ ঝগড়া করে বাড়ি থেকে তাড়িয়ে দিয়েছে' }
    ];
  }

  // 1. Marriage / Kabinnama / Document evidence
  if (
    q.includes('কাবিন') || 
    q.includes('কাবিননামা') || 
    q.includes('নিকাহনামা') || 
    (q.includes('কাগজ') && (q.includes('বিয়ে') || q.includes('বিয়ে') || cat.includes('family') || cat.includes('dower')))
  ) {
    return [
      { label: 'বাবার বাড়িতে আছে', text: 'কাবিননামার কাগজটি বাবার বাড়িতে রাখা আছে' },
      { label: 'স্বামীর কাছে আছে', text: 'কাবিননামা স্বামীর কাছে রেখে দিয়েছে, আমাকে দেয়নি' },
      { label: 'কাজী অফিসে আছে', text: 'রেজিস্ট্রি হয়েছিল, কাজী অফিসে কাবিনের নকল পাওয়া যাবে' },
      { label: 'কোনো কাগজ নেই', text: 'আমাদের কোনো লিখিত কাবিননামা বা বিয়ের কাগজ নেই' }
    ];
  }

  // 2. Dower / Dowry / Claim amount
  if (
    q.includes('দেনমোহর') || 
    (q.includes('টাকা') && (q.includes('ধার্য') || q.includes('পরিমাণ') || q.includes('দাবি'))) ||
    q.includes('কত টাকা') ||
    q.includes('টাকার পরিমাণ')
  ) {
    return [
      { label: '১ লাখ টাকা', text: 'দেনমোহর ধার্য করা হয়েছিল ১ লাখ টাকা' },
      { label: '২ লাখ টাকা', text: 'দেনমোহর ধার্য করা হয়েছিল ২ লাখ টাকা' },
      { label: '৫ লাখ টাকা', text: 'দেনমোহর ধার্য করা হয়েছিল ৫ লাখ টাকা' },
      { label: 'দেখে বলতে হবে', text: 'কাবিননামার কাগজ দেখে সঠিক টাকার পরিমাণ বলতে পারব' }
    ];
  }

  // 3. Marriage Timeline / Date / How many years
  if (
    (q.includes('বিয়ে') || q.includes('বিয়ে')) && 
    (q.includes('সন') || q.includes('কবে') || q.includes('সাল') || q.includes('বছর') || q.includes('তারিখ') || q.includes('সময়') || q.includes('সময়'))
  ) {
    return [
      { label: '১-২ বছর আগে', text: 'আনুমানিক ১ থেকে ২ বছর আগে আমাদের বিয়ে হয়েছে' },
      { label: '৪-৫ বছর আগে', text: 'আনুমানিক ৪ থেকে ৫ বছর আগে বিয়ে হয়েছিল' },
      { label: '১০+ বছর আগে', text: '১০ বছরেরও বেশি সময় আগে আমাদের বিয়ে হয়েছে' },
      { label: 'কয়েক বছর হয়েছে', text: 'সঠিক সন মনে নেই, তবে কয়েক বছর হয়ে গেছে' }
    ];
  }

  // 4. Wages / Unpaid Salary Amount
  if (
    (q.includes('মজুরি') || q.includes('বেতন') || q.includes('পাওনা')) && 
    (q.includes('টাকা') || q.includes('কত') || q.includes('বকেয়া') || q.includes('বকেয়া'))
  ) {
    return [
      { label: '১ মাসের বেতন', text: '১ মাসের পুরো মজুরি বা বেতন বকেয়া রয়েছে' },
      { label: '২-৩ মাসের বেতন', text: 'প্রায় ২ থেকে ৩ মাসের বেতন এখনও বকেয়া আছে' },
      { label: '৫-১০ হাজার টাকা', text: 'হিসাব অনুযায়ী প্রায় ৫ থেকে ১০ হাজার টাকা পাওনা আছে' },
      { label: 'হিসাব অনুযায়ী পাওনা', text: 'কাজের চুক্তি অনুযায়ী এখনো পুরো টাকা পরিশোধ করা হয়নি' }
    ];
  }

  // 5. Work Period / Duration / How long worked
  if (
    (q.includes('কাজ') || q.includes('চাকরি')) && 
    (q.includes('কতদিন') || q.includes('কবে থেকে') || q.includes('কোন সময়') || q.includes('কত মাস') || q.includes('সময়') || q.includes('সময়'))
  ) {
    return [
      { label: '১ মাস কাজ করেছি', text: 'গত ১ মাস ধরে আমি এই কাজটি করেছি' },
      { label: '৬ মাস কাজ করেছি', text: 'টানা ৬ মাস ধরে সেখানে নিয়মিত কাজ করেছি' },
      { label: '১ বছরের বেশি', text: '১ বছরেরও বেশি সময় ধরে সেখানে কাজ করেছি' },
      { label: '১০-১৫ দিনের চুক্তি', text: '১০ থেকে ১৫ দিনের নির্দিষ্ট চুক্তিভিত্তিক কাজ ছিল' }
    ];
  }

  // 6. Work Evidence / Attendance register / Slip / Witness / Sardar
  if (
    q.includes('হাজিরা') || 
    q.includes('স্লিপ') || 
    q.includes('সর্দার') || 
    q.includes('সাক্ষী') || 
    (q.includes('প্রমাণ') && cat === 'unpaid_wages')
  ) {
    return [
      { label: 'হাজিরা খাতা/স্লিপ আছে', text: 'কাজের দৈনিক হাজিরা খাতা বা স্লিপের প্রমাণ রয়েছে' },
      { label: 'সহকর্মী/সর্দার সাক্ষী', text: 'কাজের জায়গায় সহকর্মী ও সর্দার সরাসরি সাক্ষী আছেন' },
      { label: 'মৌখিক চুক্তি ছিল', text: 'শুধুমাত্র মৌখিক চুক্তি হয়েছিল, লিখিত কোনো কাগজ নেই' },
      { label: 'মালিকের তথ্য আছে', text: 'মালিক ও ঠিকাদারের পূর্ণ নাম এবং ফোন নম্বর জানা আছে' }
    ];
  }

  // 7a. Land Possession & Nature of Dispute
  if (
    (q.includes('দখল') || q.includes('দখলে') || q.includes('ওয়ারিশ') || q.includes('সীমানা') || q.includes('বেদখল') || q.includes('কারণ') || q.includes('ধরণ') || q.includes('ধরন')) &&
    (cat === 'land_dispute' || q.includes('জমি'))
  ) {
    return [
      { label: 'আমাদের দখলে আছে', text: 'জমিটি বর্তমানে আমাদের দখলেই রয়েছে' },
      { label: 'প্রতিপক্ষ দখল করেছে', text: 'প্রতিপক্ষ জোরপূর্বক জমিটি অবৈধভাবে দখল করে রেখেছে' },
      { label: 'পৈতৃক ওয়ারিশ বিরোধ', text: 'পৈতৃক ওয়ারিশ ও অংশ বণ্টন নিয়ে বিরোধ চলছে' },
      { label: 'সীমানা নিয়ে বিরোধ', text: 'জমির সীমানা নির্ধারণ ও বেদখল নিয়ে বিরোধ তৈরি হয়েছে' }
    ];
  }

  // 7b. Land Deeds / Khatian / Parcha / Records
  if (
    (q.includes('দলিল') || q.includes('খতিয়ান') || q.includes('পর্চা') || q.includes('কাগজ') || q.includes('রেজিস্ট্রি')) &&
    (cat === 'land_dispute' || q.includes('জমি'))
  ) {
    return [
      { label: 'মূল দলিল আছে', text: 'জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে' },
      { label: 'পর্চা/খতিয়ান আছে', text: 'জমির পর্চা ও খতিয়ানের সত্যায়িত কপি আছে' },
      { label: 'দলিল প্রতিপক্ষের কাছে', text: 'জমির মূল কাগজপত্র বা দলিল প্রতিপক্ষের দখলে আটকে আছে' },
      { label: 'কোনো কাগজ নেই', text: 'আমাদের কাছে বর্তমানে কোনো বৈধ দলিল বা পর্চা নেই' }
    ];
  }

  // 7c. Land Salish / Opponent / Chairman / Member
  if (
    (q.includes('সালিশ') || q.includes('মেম্বার') || q.includes('চেয়ারম্যান') || q.includes('চেয়ারম্যান') || q.includes('শরিক') || q.includes('প্রতিপক্ষ')) &&
    (cat === 'land_dispute' || q.includes('জমি'))
  ) {
    return [
      { label: 'মেম্বার/চেয়ারম্যানের সালিশ', text: 'ইউনিয়ন পরিষদে মেম্বার বা চেয়ারম্যানের কাছে সালিশ হয়েছিল কিন্তু সমাধান হয়নি' },
      { label: 'শরিকদের সাথে বিরোধ', text: 'পারিবারিক শরিক ও আত্মীয়দের সাথে জমি নিয়ে বিরোধ' },
      { label: 'বাইরের দখলদার', text: 'বাইরের প্রভাবশালী দখলদারদের সাথে বিরোধ' },
      { label: 'কোনো সালিশ হয়নি', text: 'স্থানীয়ভাবে এখনো কোনো সালিশ বা মীমাংসার বৈঠক হয়নি' }
    ];
  }

  // 7d. General Land Dispute fallback
  if (cat === 'land_dispute' || q.includes('জমি')) {
    return [
      { label: 'আমাদের দখলে আছে', text: 'জমিটি বর্তমানে আমাদের দখলেই রয়েছে' },
      { label: 'মূল দলিল আছে', text: 'জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে' },
      { label: 'প্রতিপক্ষ দখল করেছে', text: 'প্রতিপক্ষ জোরপূর্বক জমিটি অবৈধভাবে দখল করে রেখেছে' },
      { label: 'কোনো সালিশ হয়নি', text: 'স্থানীয়ভাবে এখনো কোনো সালিশ বা মীমাংসার বৈঠক হয়নি' }
    ];
  }

  // 8. Children / Maintenance / Child custody
  if (
    q.includes('সন্তান') || 
    q.includes('বাচ্চা') || 
    q.includes('ছেলে') || 
    q.includes('মেয়ে') || 
    q.includes('মেয়ে') || 
    q.includes('হেফাজত')
  ) {
    return [
      { label: '১টি সন্তান আছে', text: 'হ্যাঁ, আমাদের ১টি সন্তান আছে এবং সে আমার কাছেই থাকে' },
      { label: '২টি সন্তান আছে', text: 'হ্যাঁ, আমাদের ২টি সন্তান আছে এবং তাদের দেখাশোনা আমি করছি' },
      { label: 'কোনো সন্তান নেই', text: 'না, আমাদের কোনো সন্তান নেই' },
      { label: 'বাচ্চার খরচ দেয় না', text: 'স্বামী সন্তান বা আমার কারও কোনো ভরণপোষণ বা খরচ দেয় না' }
    ];
  }

  // 9. Current living place / Location / Father's house / Shelter
  if (
    q.includes('কোথায়') || 
    q.includes('কোথায়') || 
    q.includes('থাকেন') || 
    q.includes('বসবাস') || 
    q.includes('আলাদা') || 
    q.includes('আশ্রয়') || 
    q.includes('আশ্রয়')
  ) {
    return [
      { label: 'বাবার বাড়িতে আছি', text: 'বাধ্য হয়ে বর্তমানে বাবার বাড়িতে এসে আশ্রয় নিয়েছি' },
      { label: 'স্বামীর বাড়িতে আছি', text: 'এখনো স্বামীর বাড়িতেই আছি তবে আলাদা ঘরে থাকছি' },
      { label: 'আত্মীয়ের বাসায়', text: 'বাড়ি থেকে বের করে দেওয়ায় আত্মীয়ের বাড়িতে আশ্রয় নিয়েছি' },
      { label: 'নিরাপদ আশ্রয়ে আছি', text: 'বর্তমানে নিরাপদ জায়গায় আশ্রয় নিয়েছি' }
    ];
  }

  // 10. Police / Salish / GD / Chairman / Case
  if (
    q.includes('থানা') || 
    q.includes('জিডি') || 
    q.includes('পুলিশ') || 
    q.includes('অভিযোগ') || 
    q.includes('মামলা') || 
    q.includes('সালিশ') || 
    q.includes('মেম্বার') || 
    q.includes('চেয়ারম্যান')
  ) {
    return [
      { label: 'সালিশ হয়েছিল', text: 'স্থানীয় মেম্বার বা চেয়ারম্যানের কাছে সালিশ হয়েছিল তবে মীমাংসা হয়নি' },
      { label: 'থানায় জিডি করেছি', text: 'নিরাপত্তার স্বার্থে আগেই থানায় একটি জিডি করা হয়েছিল' },
      { label: 'কোনো অভিযোগ করিনি', text: 'এখনো পর্যন্ত থানা বা আদালতে কোনো আনুষ্ঠানিক অভিযোগ করিনি' },
      { label: 'সমাধান হয়নি', text: 'চেষ্টা করা হয়েছিল কিন্তু কোনো সুরাহা বা সমাধান হয়নি' }
    ];
  }

  // 11. Disambiguation (Problem category clarification)
  if (
    q.includes('পারিবারিক') || 
    q.includes('বকেয়া মজুরি') || 
    q.includes('বকেয়া মজুরি') || 
    q.includes('জমিজমা') || 
    q.includes('মূল ধরণ') || 
    q.includes('কোন ধরনের')
  ) {
    return [
      { label: 'দেনমোহর ও ভরণপোষণ', text: 'এটি পারিবারিক দেনমোহর ও ভরণপোষণ সংক্রান্ত দাবি' },
      { label: 'বকেয়া মজুরির দাবি', text: 'এটি কাজ করিয়ে পারিশ্রমিক বা বকেয়া মজুরি না পাওয়ার বিষয়' },
      { label: 'জমিজমা সংক্রান্ত', text: 'এটি পৈতৃক জমিজমা বা সীমানা বেদখল সংক্রান্ত বিরোধ' },
      { label: 'যৌতুক ও নির্যাতন', text: 'এটি যৌতুক দাবি ও পারিবারিক নির্যাতন সংক্রান্ত বিষয়' }
    ];
  }

  // 12. Extra fallback questions when documents absent
  if (
    q.includes('কাগজ না থাকলেও') || 
    q.includes('দলিল না থাকলেও') || 
    q.includes('চুক্তি বা স্লিপ না থাকলেও') ||
    q.includes('কাগজপত্র না থাকলেও') ||
    (q.includes('সাক্ষী') && (q.includes('কাজী') || q.includes('সর্দার') || q.includes('গ্রামের')))
  ) {
    return [
      { label: 'কাজী অফিসের তথ্য আছে', text: 'কাজী অফিসের নাম ও এলাকা আমার জানা আছে' },
      { label: 'সাক্ষী আছেন', text: 'ঘটনা বা বিয়ের প্রত্যক্ষদর্শী সাক্ষী আছেন' },
      { label: 'পরিবার জানে', text: 'পরিবার ও প্রতিবেশীরা ঘটনাটির বিষয়ে অবগত আছেন' },
      { label: 'কোনো সাক্ষী নেই', text: 'সরাসরি কোনো প্রত্যক্ষদর্শী সাক্ষী বা কাজী নেই' }
    ];
  }

  // 13. Extra fallback questions when memory/exact facts absent
  if (
    q.includes('মনে না থাকলেও') || 
    q.includes('নির্দিষ্ট মনে না থাকলেও') || 
    q.includes('আনুমানিক বা কাছাকাছি') ||
    q.includes('কোনো ধারণা কি আছে') ||
    q.includes('স্মৃতি মনে পড়ে')
  ) {
    return [
      { label: 'আনুমানিক ধারণা আছে', text: 'আনুমানিক বা কাছাকাছি টাকার পরিমাণ বা সময় আমার ধারণা আছে' },
      { label: 'পরিবারের মুরব্বিরা জানেন', text: 'পরিবারের মুরব্বিরা বা আত্মীয়রা সঠিক তথ্য দিতে পারবেন' },
      { label: 'কয়েক বছর আগে', text: 'আনুমানিক কয়েক বছর আগের ঘটনা' },
      { label: 'নির্দিষ্ট মনে নেই', text: 'একদম নির্দিষ্টভাবে কিছু মনে করতে পারছি না' }
    ];
  }

  // 14. Direct confirmation / Yes-No / Did it happen
  if (
    q.includes('কি না') || 
    q.includes('কিনা') || 
    q.includes('আছে কি') || 
    q.includes('হয়েছে কি') || 
    q.includes('হয়েছে কি না') || 
    q.includes('পেয়েছেন কি') || 
    q.includes('দিয়েছেন কি') || 
    q.endsWith('?')
  ) {
    return [
      { label: 'হ্যাঁ, আছে', text: 'হ্যাঁ, এই বিষয়ে প্রমাণ ও তথ্য আছে' },
      { label: 'না, নেই', text: 'না, এই ধরনের কোনো প্রমাণ বা তথ্য নেই' },
      { label: 'হ্যাঁ, হয়েছিল', text: 'হ্যাঁ, ঘটনাটি এইভাবেই হয়েছিল' },
      { label: 'কিছুটা পেয়েছি', text: 'কিছু অংশ দেওয়া হয়েছিল, তবে পুরোটা এখনো বাকি আছে' }
    ];
  }

  // 13. General / Safe fallback
  return [
    { label: 'হ্যাঁ, তথ্য আছে', text: 'হ্যাঁ, এই বিষয়ে প্রয়োজনীয় সব তথ্য আমার কাছে আছে' },
    { label: 'কোনো কাগজ নেই', text: 'কোনো লিখিত প্রমাণ বা কাগজপত্র নেই, সবই মৌখিক' },
    { label: 'মৌখিকভাবে হয়েছিল', text: 'সব আলোচনা ও চুক্তি মৌখিকভাবে হয়েছিল' },
    { label: 'পরামর্শ নিতে চাই', text: 'এই পরিস্থিতিতে কীভাবে অগ্রসর হব সেই আইনি পরামর্শ চাই' }
  ];
}

export const BANGLADESH_DIVISIONS: Record<string, string[]> = {
  "ঢাকা": ["ঢাকা", "গাজীপুর", "নারায়ণগঞ্জ", "মানিকগঞ্জ", "মুন্সীগঞ্জ", "নরসিংদী", "টাঙ্গাইল", "কিশোরগঞ্জ", "ফরিদপুর", "মাদারীপুর", "শরীয়তপুর", "গোপালগঞ্জ", "রাজবাড়ী"],
  "চট্টগ্রাম": ["চট্টগ্রাম", "কক্সবাজার", "কুমিল্লা", "ফেনী", "ব্রাহ্মণবাড়িয়া", "চাঁদপুর", "নোয়াখালী", "লক্ষ্মীপুর", "রাঙ্গামাটি", "খাগড়াছড়ি", "বান্দরবান"],
  "রাজশাহী": ["রাজশাহী", "বগুড়া", "পাবনা", "সিরাজগঞ্জ", "নওগাঁ", "নাটোর", "চাঁপাইনবাবগঞ্জ", "জয়পুরহাট"],
  "খুলনা": ["খুলনা", "যশোর", "সাতক্ষীরা", "বাগেরহাট", "ঝিনাইদহ", "কুষ্টিয়া", "চুয়াডাঙ্গা", "মেহেরপুর", "মাগুরা", "নড়াইল"],
  "বরিশাল": ["বরিশাল", "পটুয়াখালী", "ভোলা", "পিরোজপুর", "বরগুনা", "ঝালকাঠি"],
  "সিলেট": ["সিলেট", "মৌলভীবাজার", "হবিগঞ্জ", "সুনামগঞ্জ"],
  "রংপুর": ["রংপুর", "দিনাজপুর", "কুড়িগ্রাম", "গাইবান্ধা", "নীলফামারী", "লালমনিরহাট", "ঠাকুরগাঁও", "পঞ্চগড়"],
  "ময়মনসিংহ": ["ময়মনসিংহ", "জামালপুর", "নেত্রকোণা", "শেরপুর"]
};

export const ClientIntake: React.FC<IntakeProps> = ({ onCaseSubmitted }) => {
  const [step, setStep] = useState<'welcome' | 'recording' | 'follow_up' | 'continuation' | 'rights' | 'referral' | 'safety'>('welcome');
  const [textNarrative, setTextNarrative] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  
  // LLM Error and Retry tracking
  const [llmError, setLlmError] = useState<LlmErrorInfo | null>(null);
  const [lastAttemptedMessage, setLastAttemptedMessage] = useState<string>('');

  // Auto-dismiss floating toast notification after 10 seconds
  useEffect(() => {
    if (!llmError) return;
    const timer = setTimeout(() => {
      setLlmError(null);
    }, 10000);
    return () => clearTimeout(timer);
  }, [llmError]);

  // Session & Chat History State
  const [sessionState, setSessionState] = useState<any>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null);
  const [suggestedReplies, setSuggestedReplies] = useState<string[]>([]);
  const [continuationPrompt, setContinuationPrompt] = useState<string | null>(null);
  const [isSummarizing, setIsSummarizing] = useState<boolean>(false);
  const [safetyMessage, setSafetyMessage] = useState<string | null>(null);
  const [isSafetyCollapsed, setIsSafetyCollapsed] = useState<boolean>(false); // Starts full on first detection
  const [rightsExplanation, setRightsExplanation] = useState<string | null>(null);
  const [draftComplaint, setDraftComplaint] = useState<string | null>(null);
  const [referralInfo, setReferralInfo] = useState<{ clinic: string; slot: string } | null>(null);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [copiedDraft, setCopiedDraft] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isIntakeCompleted, setIsIntakeCompleted] = useState(false);
  const [category, setCategory] = useState<string | null>(null);
  const isOutOfScope = category === 'out_of_scope' || sessionState?.category === 'out_of_scope';
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Personal & Aggressor Info State (Collected right before Step 4 to match nearby BRAC clinic)
  const [applicantName, setApplicantName] = useState('');
  const [fatherName, setFatherName] = useState('');
  const [division, setDivision] = useState('ঢাকা');
  const [zilla, setZilla] = useState('ঢাকা');
  const [thana, setThana] = useState('');
  const [unionVillage, setUnionVillage] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [aggressorName, setAggressorName] = useState('');
  const [aggressorRelation, setAggressorRelation] = useState('স্বামী');
  const [aggressorAddress, setAggressorAddress] = useState('');
  const [isFinalizingProfile, setIsFinalizingProfile] = useState(false);
  const [profileVoiceTranscript, setProfileVoiceTranscript] = useState('');
  const [isListeningProfile, setIsListeningProfile] = useState(false);
  const [isExtractingProfile, setIsExtractingProfile] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);
  const [hasVoiceExtracted, setHasVoiceExtracted] = useState(false);
  const profileRecognitionRef = useRef<any>(null);

  const stopProfileVoiceTyping = () => {
    if (profileRecognitionRef.current) {
      try {
        profileRecognitionRef.current.stop();
      } catch (_) {}
      profileRecognitionRef.current = null;
    }
    setIsListeningProfile(false);
  };

  const handleStartNewCase = () => {
    stopVoice();
    stopProfileVoiceTyping();
    setStep('welcome');
    setTextNarrative('');
    setSafetyMessage(null);
    setIsSafetyCollapsed(false);
    setSessionState(null);
    setCategory(null);
    setChatHistory([]);
    setIsIntakeCompleted(false);
    setFollowUpQuestion(null);
    setSuggestedReplies([]);
    setRightsExplanation(null);
    setDraftComplaint(null);
    setReferralInfo(null);
    setCaseId(null);
    setApplicantName('');
    setFatherName('');
    setThana('');
    setUnionVillage('');
    setContactNumber('');
    setIsAnonymous(false);
    setAggressorName('');
    setAggressorRelation('স্বামী');
    setAggressorAddress('');
    setShowManualForm(false);
    setProfileVoiceTranscript('');
    setHasVoiceExtracted(false);
  };

  const handleExtractProfileVoice = async (textOverride?: string) => {
    const textToExtract = (textOverride || profileVoiceTranscript).trim();
    if (!textToExtract) return;

    setIsExtractingProfile(true);
    try {
      const res = await axios.post('/intake/extract_profile', {
        voice_transcript: textToExtract,
        chat_history: chatHistory
      });

      if (res.data) {
        const d = res.data;
        if (d.applicant_name) setApplicantName(d.applicant_name);
        if (d.father_name) setFatherName(d.father_name);
        
        if (d.division && BANGLADESH_DIVISIONS[d.division]) {
          setDivision(d.division);
          if (d.zilla && BANGLADESH_DIVISIONS[d.division].includes(d.zilla)) {
            setZilla(d.zilla);
          }
        } else if (d.zilla) {
          for (const [divKey, zillaList] of Object.entries(BANGLADESH_DIVISIONS)) {
            if (zillaList.includes(d.zilla)) {
              setDivision(divKey);
              setZilla(d.zilla);
              break;
            }
          }
        }
        
        if (d.thana) setThana(d.thana);
        if (d.union_village) setUnionVillage(d.union_village);
        if (d.contact_number) setContactNumber(d.contact_number);
        if (d.aggressor_name) setAggressorName(d.aggressor_name);
        if (d.aggressor_relation) setAggressorRelation(d.aggressor_relation);
        if (d.aggressor_address) setAggressorAddress(d.aggressor_address);
        setHasVoiceExtracted(true);
      }
    } catch (err) {
      console.error('Failed to extract profile from voice:', err);
    } finally {
      setIsExtractingProfile(false);
    }
  };

  const startProfileVoiceTyping = async () => {
    stopVoice();
    const SpeechRecognitionClass =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setLlmError({
        title: 'ভয়েস টাইপিং অনুপলব্ধ',
        message: 'আপনার ব্রাউজারে ভয়েস টাইপিং সমর্থিত নয়। অনুগ্রহ করে Google Chrome বা Edge ব্রাউজার ব্যবহার করুন।',
        errorType: 'compatibility_error'
      });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
    } catch (err: any) {
      setLlmError({
        title: 'মাইক্রোফোনের অনুমতি প্রয়োজন',
        message: 'মাইক্রোফোনের অনুমতি দেওয়া হয়নি। ব্রাউজার সেটিংসে Microphone "Allow" করুন।',
        errorType: 'permission_error'
      });
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.lang = 'bn-BD';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      let currentAccumulated = profileVoiceTranscript.trim();

      recognition.onstart = () => {
        setIsListeningProfile(true);
      };

      recognition.onresult = (event: any) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          const transcript = item[0]?.transcript || '';
          if (item.isFinal) {
            currentFinal += transcript;
          } else {
            currentInterim += transcript;
          }
        }

        if (currentFinal) {
          currentAccumulated = currentAccumulated
            ? `${currentAccumulated} ${currentFinal.trim()}`
            : currentFinal.trim();
        }

        const fullDisplay = [currentAccumulated, currentInterim.trim()].filter(Boolean).join(' ');
        setProfileVoiceTranscript(fullDisplay);
      };

      recognition.onerror = () => {
        setIsListeningProfile(false);
      };

      recognition.onend = () => {
        setIsListeningProfile(false);
        if (currentAccumulated.trim()) {
          handleExtractProfileVoice(currentAccumulated.trim());
        }
      };

      profileRecognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      console.warn('Profile voice recognition start error:', e);
      setIsListeningProfile(false);
    }
  };

  const handleSampleVoiceProfile = () => {
    const sample = "আমার নাম মোসাম্মৎ রহিমা খাতুন, বাবার নাম আবদুল করিম। আমার বাড়ি কুমিল্লার চান্দিনা উপজেলার বাতাঘাসী গ্রামে। বিবাদী আমার স্বামী রফিকুল ইসলাম, সে চান্দিনা বাজারে থাকে। আমার মোবাইল নম্বর ০১৭১২৩৪৫৬৭৮";
    setProfileVoiceTranscript(sample);
    handleExtractProfileVoice(sample);
  };

  // Auto prefill extracted names from sessionState if available
  useEffect(() => {
    if (sessionState?.applicant_name && sessionState.applicant_name !== '[নাম সংরক্ষিত]' && !applicantName) {
      setApplicantName(sessionState.applicant_name);
    }
    if (sessionState?.respondent && sessionState.respondent !== '[বিবাদী]' && !aggressorName) {
      setAggressorName(sessionState.respondent);
    }
  }, [sessionState]);

  const handleQuickFillProfile = () => {
    setApplicantName('মোসাম্মৎ রহিমা খাতুন');
    setFatherName('মোঃ করিম মিয়া');
    setDivision('চট্টগ্রাম');
    setZilla('কুমিল্লা');
    setThana('চৌদ্দগ্রাম');
    setUnionVillage('কাশিনগর ইউনিয়ন, ৪নং ওয়ার্ড');
    setContactNumber('০১৭০০-১১২২৩৩');
    setAggressorName('মোঃ আলমগীর হোসেন');
    setAggressorRelation('স্বামী');
    setAggressorAddress('উত্তরপাড়া, কাশিনগর, চৌদ্দগ্রাম, কুমিল্লা');
  };

  const handleFinalizeProfile = async () => {
    setIsFinalizingProfile(true);
    try {
      const payload = {
        case_id: caseId || sessionState?.case_id,
        session_state: sessionState,
        applicant_name: isAnonymous ? '[নাম সংরক্ষিত]' : (applicantName.trim() || 'আবেদনকারী'),
        father_name: fatherName.trim() || undefined,
        division: division || 'ঢাকা',
        zilla: zilla || 'ঢাকা',
        thana: thana.trim() || 'সদর',
        union_village: unionVillage.trim() || 'সদর ইউনিয়ন',
        contact_number: contactNumber.trim() || undefined,
        is_anonymous: isAnonymous,
        aggressor_name: aggressorName.trim() || undefined,
        aggressor_relation: aggressorRelation || undefined,
        aggressor_address: aggressorAddress.trim() || undefined
      };

      const res = await axios.post('/api/intake/finalize_profile', payload);
      if (res.data) {
        if (res.data.referral_clinic) {
          setReferralInfo({
            clinic: res.data.referral_clinic,
            slot: res.data.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
        }
        if (res.data.draft_complaint) {
          setDraftComplaint(res.data.draft_complaint);
        }
        if (res.data.rights_explanation) {
          setRightsExplanation(res.data.rights_explanation);
        }
        if (res.data.session_state) {
          setSessionState(res.data.session_state);
        }
        if (res.data.case_id) {
          setCaseId(res.data.case_id);
        }
      }
      stopVoice();
      // Rights step commented out, route directly to referral
      setStep('referral');
    } catch (err) {
      console.error('Finalize profile error:', err);
      stopVoice();
      setStep('referral');
    } finally {
      setIsFinalizingProfile(false);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isStreaming]);

  const handleCopyDraft = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedDraft(true);
    setTimeout(() => setCopiedDraft(false), 2500);
  };

  const handleDownloadDraftPdf = async () => {
    if (!draftComplaint) return;
    try {
      setIsDownloadingPdf(true);
      const appName = isAnonymous ? '[নাম সংরক্ষিত]' : (applicantName.trim() || sessionState?.applicant_name || '[নাম সংরক্ষিত]');
      const aggText = aggressorName.trim() 
        ? `${aggressorName.trim()}${aggressorRelation ? ` (সম্পর্ক: ${aggressorRelation})` : ''}` 
        : (sessionState?.respondent || '[বিবাদী]');
      const addr = [unionVillage, thana, zilla, division].filter(Boolean).join(', ') || sessionState?.address || '[ঠিকানা — অপ্রতিষ্ঠিত]';

      await downloadDraftPdf({
        draftText: draftComplaint,
        caseId: caseId || sessionState?.case_id,
        category: sessionState?.category,
        applicantName: appName,
        respondent: aggText,
        address: addr,
        clinicName: referralInfo?.clinic || sessionState?.referral_clinic,
        appointmentSlot: referralInfo?.slot || sessionState?.referral_slot,
        status: safetyMessage ? 'URGENT' : 'New'
      });
    } catch (err: any) {
      console.error('PDF Generation Error:', err);
      setLlmError({
        title: 'পিডিএফ তৈরিতে সমস্যা',
        message: 'পিডিএফ তৈরিতে সমস্যা হয়েছে: ' + (err?.message || 'অনুগ্রহ করে পুনরায় চেষ্টা করুন।'),
        errorType: 'pdf_error'
      });
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handlePrintDraft = () => {
    if (!draftComplaint) return;
    const appName = isAnonymous ? '[নাম সংরক্ষিত]' : (applicantName.trim() || sessionState?.applicant_name || '[নাম সংরক্ষিত]');
    const aggText = aggressorName.trim() 
      ? `${aggressorName.trim()}${aggressorRelation ? ` (সম্পর্ক: ${aggressorRelation})` : ''}` 
      : (sessionState?.respondent || '[বিবাদী]');
    const addr = [unionVillage, thana, zilla, division].filter(Boolean).join(', ') || sessionState?.address || '[ঠিকানা — অপ্রতিষ্ঠিত]';

    printDraftPdf({
      draftText: draftComplaint,
      caseId: caseId || sessionState?.case_id,
      category: sessionState?.category,
      applicantName: appName,
      respondent: aggText,
      address: addr,
      clinicName: referralInfo?.clinic || sessionState?.referral_clinic,
      appointmentSlot: referralInfo?.slot || sessionState?.referral_slot,
      status: safetyMessage ? 'URGENT' : 'New'
    });
  };

  // Audio Playback / Voice Output (TTS) State
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [currentPlayingText, setCurrentPlayingText] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stopVoice = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setIsLoadingAudio(false);
    setCurrentPlayingText(null);
  };

  const playVoice = async (text: string) => {
    if (!text || !text.trim()) return;

    // Toggle stop if already playing or loading the same text
    if ((isPlayingAudio || isLoadingAudio) && currentPlayingText === text) {
      stopVoice();
      return;
    }

    stopVoice();
    setIsLoadingAudio(true);
    setCurrentPlayingText(text);

    try {
      // 1. Prepare stream via POST to avoid HTTP 431 URL length limits on long text
      const res = await axios.post('/api/tts/prepare', { text: text.trim() });
      const streamUrl = res.data.audio_url;

      const audio = new Audio(streamUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(true);
      };

      audio.onended = () => {
        setIsPlayingAudio(false);
        setIsLoadingAudio(false);
        setCurrentPlayingText(null);
        audioRef.current = null;
      };

      audio.onerror = (e) => {
        console.warn('Audio streaming failed, trying fallback:', e);
        setIsLoadingAudio(false);
        playBrowserSpeechFallback(text);
      };

      await audio.play();
    } catch (err) {
      console.warn('TTS prepare failed, falling back to direct GET:', err);
      try {
        const audioUrl = `/api/tts?text=${encodeURIComponent(text.trim().slice(0, 500))}`;
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onplay = () => {
          setIsLoadingAudio(false);
          setIsPlayingAudio(true);
        };

        audio.onended = () => {
          setIsPlayingAudio(false);
          setIsLoadingAudio(false);
          setCurrentPlayingText(null);
          audioRef.current = null;
        };

        audio.onerror = () => {
          setIsLoadingAudio(false);
          playBrowserSpeechFallback(text);
        };

        await audio.play();
      } catch {
        setIsLoadingAudio(false);
        playBrowserSpeechFallback(text);
      }
    }
  };

  const playBrowserSpeechFallback = (text: string) => {
    if (!('speechSynthesis' in window)) {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
      return;
    }
    const cleanText = text.replace(/[*#_`]/g, '').slice(0, 300);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'bn-BD';
    const voices = window.speechSynthesis.getVoices();
    const bnVoice = voices.find((v) => v.lang.startsWith('bn'));
    if (bnVoice) utterance.voice = bnVoice;
    utterance.rate = 0.92;
    utterance.onend = () => {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
    };
    utterance.onerror = () => {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
    };
    window.speechSynthesis.speak(utterance);
  };

  // 100% Pure Frontend Voice Typing (Browser-Native Web Speech API - Zero backend overhead)
  const [isListening, setIsListening] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const timerIntervalRef = useRef<any>(null);
  const shouldBeListeningRef = useRef<boolean>(false);
  const accumulatedTextRef = useRef<string>('');

  const stopVoiceTyping = () => {
    shouldBeListeningRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    setIsListening(false);
  };

  const startVoiceTyping = async () => {
    stopVoice(); // Stop any TTS speech playback
    setVoiceStatus(null);

    const SpeechRecognitionClass =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setVoiceStatus('আপনার ব্রাউজারে ভয়েস টাইপিং সমর্থিত নয়। অনুগ্রহ করে Google Chrome বা Edge ব্রাউজার ব্যবহার করুন।');
      setLlmError({
        title: 'ভয়েস টাইপিং অনুপলব্ধ',
        message: 'আপনার ব্রাউজারে ভয়েস টাইপিং সমর্থিত নয়। অনুগ্রহ করে Google Chrome বা Edge ব্রাউজার ব্যবহার করুন।',
        errorType: 'compatibility_error'
      });
      return;
    }

    try {
      // Explicitly request mic access so browser prompts "Allow" cleanly
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Immediately release tracks so SpeechRecognition has full exclusive access to the microphone
      stream.getTracks().forEach((track) => track.stop());
    } catch (err: any) {
      console.warn('Microphone permission denied:', err);
      setVoiceStatus('মাইক্রোফোনের অনুমতি প্রয়োজন। ব্রাউজারে Microphone "Allow" করুন।');
      setLlmError({
        title: 'মাইক্রোফোনের অনুমতি প্রয়োজন',
        message: 'মাইক্রোফোনের অনুমতি দেওয়া হয়নি। ব্রাউজার সেটিংসে Microphone "Allow" করুন।',
        errorType: 'permission_error'
      });
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.lang = 'bn-BD';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      // Preserve already typed text
      accumulatedTextRef.current = textNarrative.trim();

      recognition.onstart = () => {
        setIsListening(true);
        shouldBeListeningRef.current = true;
        setVoiceStatus('কথা বলুন, আপনার কথা সরাসরি বাংলায় লেখা হচ্ছে...');
        setRecordingSeconds(0);
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event: any) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          const transcript = item[0]?.transcript || '';
          if (item.isFinal) {
            currentFinal += transcript;
          } else {
            currentInterim += transcript;
          }
        }

        if (currentFinal) {
          accumulatedTextRef.current = accumulatedTextRef.current
            ? `${accumulatedTextRef.current} ${currentFinal.trim()}`
            : currentFinal.trim();
        }

        const fullDisplay = [accumulatedTextRef.current, currentInterim.trim()]
          .filter(Boolean)
          .join(' ')
          .trim();

        setTextNarrative(fullDisplay);
      };

      recognition.onerror = (event: any) => {
        console.warn('[SpeechRecognition Error]', event.error);
        if (event.error === 'no-speech') {
          // Harmless pause in speech, ignore so auto-restart continues
          return;
        }
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setVoiceStatus('মাইক্রোফোনের অনুমতি পাওয়া যায়নি। ব্রাউজার সেটিংসে গিয়ে পারমিশন দিন।');
          return;
        }
        if (event.error === 'aborted') {
          return;
        }
        setVoiceStatus(`ভয়েস টাইপিং সাময়িক ব্যাহত (${event.error})। আবার কথা বলুন।`);
      };

      recognition.onend = () => {
        // Auto-restart if user has not explicitly tapped "থামান"
        if (shouldBeListeningRef.current) {
          try {
            recognition.start();
          } catch (_) {}
        } else {
          setIsListening(false);
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
          setVoiceStatus('ভয়েস টাইপিং সম্পন্ন। নিচের টেক্সটটি যাচাই করে জমা দিন।');
        }
      };

      recognitionRef.current = recognition;
      shouldBeListeningRef.current = true;
      recognition.start();
    } catch (err: any) {
      console.error('Speech recognition start failed:', err);
      setVoiceStatus('ভয়েস টাইপিং শুরু করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।');
      setIsListening(false);
      shouldBeListeningRef.current = false;
    }
  };

  useEffect(() => {
    return () => {
      stopVoiceTyping();
      stopVoice();
    };
  }, []);

  const renderVoiceTypingButton = () => {
    const isGenerating = isLoading || isStreaming;
    return (
      <button
        type="button"
        disabled={isGenerating}
        onClick={isListening ? stopVoiceTyping : startVoiceTyping}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          fontSize: '13px',
          fontWeight: '600',
          borderRadius: '20px',
          border: isGenerating ? '1px solid #e2e8f0' : (isListening ? '1px solid #ef4444' : '1px solid #bae6fd'),
          cursor: isGenerating ? 'not-allowed' : 'pointer',
          backgroundColor: isGenerating ? '#f8fafc' : (isListening ? '#fef2f2' : '#f0f9ff'),
          color: isGenerating ? '#94a3b8' : (isListening ? '#b91c1c' : '#0284c7'),
          opacity: isGenerating ? 0.6 : 1,
          transition: 'all 0.15s ease'
        }}
        title={isListening ? 'রেকর্ডিং বন্ধ করুন' : (isGenerating ? 'অপেক্ষা করুন...' : 'মুখে বলে বাংলায় লিখুন')}
      >
      {isListening ? (
        <>
          <span className="mic-recording-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block' }} />
          <Square size={13} fill="#dc2626" />
          <span>থামান ({String(Math.floor(recordingSeconds / 60)).padStart(2, '0')}:{String(recordingSeconds % 60).padStart(2, '0')})</span>
        </>
      ) : (
        <>
          <Mic size={14} />
          <span>মুখে বলুন (Voice Typing)</span>
        </>
      )}
    </button>
    );
  };


  const handleSummarizeAndContinue = async () => {
    let textToSummarize = lastAttemptedMessage.trim() || textNarrative.trim();
    if (!textToSummarize) {
      for (let i = chatHistory.length - 1; i >= 0; i--) {
        if (chatHistory[i].role === 'user' && chatHistory[i].content.trim()) {
          textToSummarize = chatHistory[i].content.trim();
          break;
        }
      }
    }
    if (!textToSummarize) {
      handleSendMessage("", true, false);
      return;
    }

    try {
      setIsSummarizing(true);
      const res = await axios.post('/api/intake/summarize', {
        transcript: textToSummarize,
        existing_state: sessionState
      });
      const summarizedText = res.data.summarized_text;
      setIsSummarizing(false);
      setContinuationPrompt(null);

      if (summarizedText) {
        // Update user message in chatHistory to indicate it was summarized
        setChatHistory((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i--) {
            if (next[i].role === 'user') {
              next[i] = {
                ...next[i],
                content: `${summarizedText}\n\n[✨ অতিরিক্ত টোকেন এড়াতে এআই দ্বারা সংক্ষেপিত]`
              };
              break;
            }
          }
          return next;
        });

        // Run intake with summarized text
        await handleSendMessage(summarizedText, false, true);
      } else {
        await handleSendMessage("", true, false);
      }
    } catch (err) {
      console.error('Summarization failed, proceeding with standard continuation:', err);
      setIsSummarizing(false);
      setContinuationPrompt(null);
      await handleSendMessage("", true, false);
    }
  };

  const handleEditNarrative = () => {
    let textToEdit = lastAttemptedMessage.trim() || textNarrative.trim();
    if (!textToEdit) {
      for (let i = chatHistory.length - 1; i >= 0; i--) {
        if (chatHistory[i].role === 'user' && chatHistory[i].content.trim()) {
          textToEdit = chatHistory[i].content.trim();
          break;
        }
      }
    }
    stopVoice();
    setTextNarrative(textToEdit);
    setContinuationPrompt(null);
    setChatHistory((prev) => prev.filter(m => m.content.trim() !== ''));
    setStep('follow_up');
  };

  const handleRetryMessage = (content: string, failedIndex?: number) => {
    if (failedIndex !== undefined) {
      setChatHistory((prev) => prev.filter((_, idx) => idx !== failedIndex));
    }
    handleSendMessage(content);
  };

  const handleSendMessage = async (textToSend?: string, isContinuation: boolean = false, isSummarized: boolean = false) => {
    stopVoiceTyping();
    const message = textToSend !== undefined ? textToSend : textNarrative;
    if (!message.trim() && !isContinuation) return;

    stopVoice();
    setVoiceStatus(null);
    setLlmError(null);
    setContinuationPrompt(null);
    if (!sessionState) {
      setSafetyMessage(null);
      setIsSafetyCollapsed(false);
    } else if (safetyMessage) {
      // User is answering follow-up questions after seeing safety banner once -> Auto-collapse on second turn!
      setIsSafetyCollapsed(true);
    }
    setLastAttemptedMessage(message || "");
    setIsLoading(true);
    setIsStreaming(true);
    setStreamStatus('বিবরণ বিশ্লেষণ ও আইনি তথ্য যাচাই করা হচ্ছে...');

    // Optimistically push the user's message and an active assistant placeholder
    if (message.trim()) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: message.trim() },
        { role: 'assistant', content: '' }
      ]);
    }
    setTextNarrative('');
    setSuggestedReplies([]);
    setFollowUpQuestion(null);

    // Switch to conversational view immediately so the user sees live activity
    if (step === 'recording' || step === 'continuation') {
      setStep('follow_up');
    }

    try {
      // Connect to SSE streaming endpoint
      const response = await fetch('/api/intake/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: message || "",
          existing_state: sessionState,
          is_continuation: isContinuation,
          is_summarized: isSummarized
        })
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming connection failed, activating fallback');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedAssistantText = '';
      let finalData: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const jsonStr = trimmed.replace('data: ', '').trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);
            if (event.type === 'status') {
              setStreamStatus(event.content);
            } else if (event.type === 'error') {
              const errDetails = event.llm_error_details || {};
              setLlmError({
                title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
                message: event.llm_error || errDetails.message_bn || 'এআই মডেলের সাথে যোগাযোগে ত্রুটি ঘটেছে।',
                code: errDetails.status_code || errDetails.error_type || 500,
                details: errDetails.message_en || errDetails.raw_error || '',
                errorType: errDetails.error_type
              });
              setStreamStatus(null);
            } else if (event.type === 'token') {
              accumulatedAssistantText += event.content;
              setStreamStatus(null);
              setChatHistory((prev) => {
                const copy = [...prev];
                if (copy.length > 0 && copy[copy.length - 1].role === 'assistant') {
                  copy[copy.length - 1] = { role: 'assistant', content: accumulatedAssistantText };
                }
                return copy;
              });
            } else if (event.type === 'final') {
              finalData = event;
            }
          } catch (e) {
            console.error('SSE token parse error:', e);
          }
        }
      }

      // Process any remaining data in the buffer after reading stream
      if (buffer.trim()) {
        const remainingLines = buffer.split('\n');
        for (const rLine of remainingLines) {
          const trimmed = rLine.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const jsonStr = trimmed.replace('data: ', '').trim();
          if (!jsonStr) continue;
          try {
            const event = JSON.parse(jsonStr);
            if (event.type === 'token') {
              accumulatedAssistantText += event.content;
            } else if (event.type === 'final') {
              finalData = event;
            }
          } catch (e) {
            console.error('Buffer flush parse error:', e);
          }
        }
      }

      if (!finalData) {
        throw new Error('Streaming stream closed without final event payload');
      }

      if (finalData) {
        if (finalData.llm_error) {
          const errDetails = finalData.llm_error_details || {};
          setLlmError({
            title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
            message: finalData.llm_error,
            code: errDetails.status_code || errDetails.error_type || 500,
            details: errDetails.message_en || errDetails.raw_error || '',
            errorType: errDetails.error_type
          });
          setChatHistory((prev) => {
            const cleaned = prev.filter(m => m.content.trim() !== '');
            const lastUserIdx = cleaned.map(m => m.role).lastIndexOf('user');
            if (lastUserIdx !== -1) {
              const updated = [...cleaned];
              updated[lastUserIdx] = { ...updated[lastUserIdx], failed: true };
              return updated;
            }
            return cleaned;
          });
          return;
        }

        setSessionState(finalData.session_state);
        if (finalData.category) {
          setCategory(finalData.category);
        } else if (finalData.session_state?.category) {
          setCategory(finalData.session_state.category);
        }
        if (finalData.chat_history && finalData.chat_history.length > 0) {
          setChatHistory(finalData.chat_history);
        }

        // 1. Safety Information Handling (Only show helpline on active/immediate danger)
        if (finalData.safety_flag) {
          if (!safetyMessage) {
            setIsSafetyCollapsed(false); // First detection -> show full expanded card
          }
          setSafetyMessage(finalData.safety_message);
          onCaseSubmitted();
        } else {
          setSafetyMessage(null);
          setIsSafetyCollapsed(false);
        }

        // 2. Token Budget Continuation
        if (finalData.requires_continuation) {
          setContinuationPrompt(finalData.continuation_prompt);
          setStep('follow_up');
          return;
        }

        // 3. Follow-up or Legal Rights Solution
        if (finalData.suggested_replies && finalData.suggested_replies.length > 0) {
          setSuggestedReplies(finalData.suggested_replies);
        }
        if (finalData.follow_up_question) {
          setFollowUpQuestion(finalData.follow_up_question);
          setIsIntakeCompleted(false);
          setStep('follow_up');
        } else if (finalData.is_complete) {
          setRightsExplanation(finalData.rights_explanation);
          setDraftComplaint(finalData.draft_complaint);
          setReferralInfo({
            clinic: finalData.referral_clinic || 'ব্র্যাক আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: finalData.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(finalData.case_id);
          setIsIntakeCompleted(true);
          setFollowUpQuestion(null);
          setSuggestedReplies([]);
          setTextNarrative('');
          setStep('follow_up');
          onCaseSubmitted();
        }
      }
    } catch (err) {
      console.warn('Streaming failed or incomplete, fallback to standard endpoint:', err);
      // Seamless fallback to standard HTTP endpoint
      try {
        const fallbackRes = await axios.post('/api/intake/message', {
          transcript: message || "",
          existing_state: sessionState,
          is_continuation: isContinuation,
          is_summarized: isSummarized
        });

        const data = fallbackRes.data;
        if (data.llm_error) {
          const errDetails = data.llm_error_details || {};
          setLlmError({
            title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
            message: data.llm_error,
            code: errDetails.status_code || errDetails.error_type || 500,
            details: errDetails.message_en || errDetails.raw_error || '',
            errorType: errDetails.error_type
          });
          setChatHistory((prev) => {
            const cleaned = prev.filter(m => m.content.trim() !== '');
            const lastUserIdx = cleaned.map(m => m.role).lastIndexOf('user');
            if (lastUserIdx !== -1) {
              const updated = [...cleaned];
              updated[lastUserIdx] = { ...updated[lastUserIdx], failed: true };
              return updated;
            }
            return cleaned;
          });
          return;
        }

        setSessionState(data.session_state);
        if (data.category) {
          setCategory(data.category);
        } else if (data.session_state?.category) {
          setCategory(data.session_state.category);
        }

        if (data.chat_history && data.chat_history.length > 0) {
          setChatHistory(data.chat_history);
        }

        // 1. Safety Information Handling (Only show helpline on active/immediate danger)
        if (data.safety_flag) {
          if (!safetyMessage) {
            setIsSafetyCollapsed(false); // First detection -> show full expanded card
          }
          setSafetyMessage(data.safety_message);
          onCaseSubmitted();
        } else {
          setSafetyMessage(null);
          setIsSafetyCollapsed(false);
        } 
        
        if (data.requires_continuation) {
          setContinuationPrompt(data.continuation_prompt);
          setStep('follow_up');
        } else if (data.follow_up_question) {
          if (data.suggested_replies && data.suggested_replies.length > 0) {
            setSuggestedReplies(data.suggested_replies);
          }
          setFollowUpQuestion(data.follow_up_question);
          setIsIntakeCompleted(false);
          setStep('follow_up');
        } else if (data.is_complete) {
          setRightsExplanation(data.rights_explanation);
          setDraftComplaint(data.draft_complaint);
          setReferralInfo({
            clinic: data.referral_clinic || 'ব্র্যাক আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: data.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(data.case_id);
          setIsIntakeCompleted(true);
          setFollowUpQuestion(null);
          setSuggestedReplies([]);
          setTextNarrative('');
          setStep('follow_up');
          onCaseSubmitted();
        }
      } catch (fallbackErr: any) {
        console.error('Fallback endpoint also failed:', fallbackErr);
        let errorTitle = 'সার্ভার সংযোগ ত্রুটি';
        let errorMsg = 'সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না।';
        let errCode: string | number = 'CONNECTION_ERROR';
        let errDetails = '';
        let errType = 'connection_error';

        let troubleshootingList: string[] | undefined;

        if (fallbackErr.response) {
          const status = fallbackErr.response.status;
          errCode = status;
          const detail = fallbackErr.response.data?.detail;
          if (detail && typeof detail === 'object') {
            errorTitle = detail.title || errorTitle;
            errorMsg = detail.message_bn || detail.message || errorMsg;
            errType = detail.error_type || errType;
            troubleshootingList = detail.troubleshooting_bn;
            errDetails = detail.message_en || detail.error || '';
          } else if (typeof detail === 'string') {
            errorMsg = detail;
            errDetails = detail;
          } else if (status === 401) {
            errorTitle = 'এলএলএম অথেন্টিকেশন ত্রুটি (Error 401 Unauthorized)';
            errorMsg = 'এআই মডেলের API কী বা ক্রেডেনশিয়াল সঠিক নয়। backend/.env ফাইলে সেটিংস (Local / Vertex AI / OpenRouter) যাচাই করুন।';
            errDetails = 'Invalid, missing, or expired API token (HTTP 401 Unauthorized).';
            errType = 'authentication_error';
          } else if (status === 429) {
            errorTitle = 'টোকেন কোটা বা রেট লিমিট অতিক্রম (Error 429)';
            errorMsg = 'টোকেন কোটা শেষ অথবা রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ পর পুনরায় চেষ্টা করুন।';
            errDetails = 'Rate limit reached or token quota exhausted (HTTP 429 Rate Limit).';
            errType = 'rate_limit_error';
          } else if (status === 402) {
            errorTitle = 'টোকেন ব্যালেন্স ত্রুটি (Error 402 Payment Required)';
            errorMsg = 'আপনার একাউন্টে পর্যাপ্ত টোকেন ব্যালেন্স বা ক্রেডিট নেই। অনুগ্রহ করে টোকেন রিচার্জ করুন।';
            errDetails = 'Insufficient token credits or balance (HTTP 402).';
            errType = 'token_credit_error';
          }
        } else if (fallbackErr.request) {
          errorTitle = 'এলএলএম / সার্ভার সংযোগ বিচ্ছিন্ন (Not Connected)';
          errorMsg = 'এআই মডেল বা ব্যাকএন্ড সার্ভারের সাথে সংযোগ স্থাপন সম্ভব হয়নি। অনুগ্রহ করে ইন্টারনেট ও সার্ভার চালু আছে কি না দেখুন।';
          errDetails = fallbackErr.message || 'Network connection failed.';
          errType = 'connection_error';
        }

        setLlmError({
          title: errorTitle,
          message: errorMsg,
          code: errCode,
          details: errDetails,
          errorType: errType,
          troubleshooting: troubleshootingList
        });
        setChatHistory((prev) => {
          const cleaned = prev.filter(m => m.content.trim() !== '');
          const lastUserIdx = cleaned.map(m => m.role).lastIndexOf('user');
          if (lastUserIdx !== -1) {
            const updated = [...cleaned];
            updated[lastUserIdx] = { ...updated[lastUserIdx], failed: true };
            return updated;
          }
          return cleaned;
        });
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamStatus(null);
    }
  };

  // Quick fill sample narratives for demo
  const handleLoadSample = (sampleType: 'dower' | 'wages' | 'violence' | 'long') => {
    if (sampleType === 'dower') {
      setTextNarrative("আমার বিয়ে হয়েছে ছয় বছর হলো। দুই বছর ধরে আমার স্বামী আলাদা থাকে, কোনো খরচ দেয় না। আমি বাচ্চা নিয়ে বাবার বাড়িতে আছি। কাবিনে লেখা ছিল দুই লাখ টাকা, এক টাকাও পাইনি। ফোন করলে বলে টাকা নাই। আমি আর কতদিন বাবার ঘাড়ে বসে থাকব?");
    } else if (sampleType === 'wages') {
      setTextNarrative("ধান কাটার কাজ করছিলাম, দশ দিন। দিন হাজিরা সাড়ে পাঁচশ টাকা কথা ছিল। কাজ শেষে দিল তিন হাজার, বাকিটা পরে দিবে বলল। দুই মাস হয়ে গেছে। লিখিত কিছু নাই, গ্রামের লোক সবাই জানে।");
    } else if (sampleType === 'violence') {
      setTextNarrative("কাবিনের টাকা তো পাইনিই, উল্টো গত সপ্তাহে হাত ভেঙে দিয়েছে। ডাক্তারের কাছে যেতেও দেয়নি। আজকেও বলছে রাতে দেখে নিবে। আমি খুব ভয় পাচ্ছি।");
    } else if (sampleType === 'long') {
      setTextNarrative("চার বছর আগে আমার বিয়ে হয়েছে। বিয়ের পর থেকে ওরা আমার বাবার কাছে বারবার যৌতুকের জন্য টাকা চাইতে থাকে। বাবা জমি বিক্রি করে কিছু টাকা দিয়েছেন, প্রায় আশি হাজার টাকা। তারপরও ওদের চাওয়া শেষ হয় না। কাবিনের টাকা আজও এক পয়সাও পাইনি। এখন ওরা আমাকে এবং আমার ছোট মেয়েকে বাড়ি ছেড়ে চলে যেতে বাধ্য করতেছে। শাশুড়ি ও ভাশুররা হুমকি দিচ্ছে। কাবিননামার কাগজ বাবার কাছে রাখা আছে। আমি এখন কোথায় যাব, কী করব কিছুই বুঝতে পারছি না।");
    }
  };

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto' }}>
      {/* STEP PROGRESS WIZARD */}
      <div className="stepper-container">
        <div className={`step-item ${step === 'welcome' ? 'active' : 'completed'}`}>
          <div className="step-circle">{step === 'welcome' ? '১' : <Check size={14} />}</div>
          <span className="step-label">স্বাগতম</span>
        </div>
        <div className={`step-line ${['recording', 'follow_up', 'continuation', 'rights', 'referral'].includes(step) ? 'active' : ''}`} />
        <div className={`step-item ${step === 'recording' ? 'active' : ['follow_up', 'continuation', 'rights', 'referral'].includes(step) ? 'completed' : ''}`}>
          <div className="step-circle">{['follow_up', 'continuation', 'rights', 'referral'].includes(step) ? <Check size={14} /> : '২'}</div>
          <span className="step-label">বিবরণ</span>
        </div>
        <div className={`step-line ${['follow_up', 'continuation', 'rights', 'referral'].includes(step) ? 'active' : ''}`} />
        <div className={`step-item ${['follow_up', 'continuation'].includes(step) ? 'active' : ['rights', 'referral'].includes(step) ? 'completed' : ''}`}>
          <div className="step-circle">{['rights', 'referral'].includes(step) ? <Check size={14} /> : '৩'}</div>
          <span className="step-label">{isOutOfScope ? 'আওতাভুক্ত নয়' : (isIntakeCompleted ? 'প্রোফাইল' : 'প্রশ্নোত্তর')}</span>
        </div>
        <div className={`step-line ${['rights', 'referral'].includes(step) ? 'active' : ''}`} />
        <div className={`step-item ${['rights', 'referral'].includes(step) ? 'active' : ''}`}>
          <div className="step-circle">৪</div>
          <span className="step-label">ক্লিনিক ও আবেদন</span>
        </div>
      </div>

      {/* URGENT SAFETY & EMERGENCY HELPLINE RIBBON (Collapsible & Non-blocking) */}
      {safetyMessage && (
        <div 
          style={{ 
            border: '1.5px solid #fca5a5', 
            borderLeft: '5px solid #e11d48',
            backgroundColor: '#fff1f2', 
            borderRadius: '10px',
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(225, 29, 72, 0.08)',
            padding: isSafetyCollapsed ? '8px 14px' : '14px 18px',
            transition: 'all 0.2s ease-in-out'
          }}
        >
          {isSafetyCollapsed ? (
            /* COMPACT SLIM RIBBON (Only ~40px high) */
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flexWrap: 'wrap' }}>
                <AlertTriangle size={18} color="#e11d48" style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '13.5px', fontWeight: '700', color: '#be123c', whiteSpace: 'nowrap' }}>
                  জরুরি হেল্পলাইন:
                </span>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => window.open('tel:16430')}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: '#e11d48',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '5px',
                      padding: '3px 9px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                    title="১৬৪৩০-এ কল করুন"
                  >
                    <PhoneCall size={12} /> ১৬৪৩০
                  </button>
                  <button
                    onClick={() => window.open('tel:109')}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: '#ffffff',
                      color: '#be123c',
                      border: '1px solid #fda4af',
                      borderRadius: '5px',
                      padding: '3px 8px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                    title="১০৯-এ কল করুন"
                  >
                    <PhoneCall size={12} /> ১০৯
                  </button>
                  <button
                    onClick={() => window.open('tel:999')}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: '#ffffff',
                      color: '#be123c',
                      border: '1px solid #fda4af',
                      borderRadius: '5px',
                      padding: '3px 8px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}
                    title="৯৯৯-এ কল করুন"
                  >
                    <PhoneCall size={12} /> ৯৯৯
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={() => playVoice(safetyMessage)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '12px',
                    padding: '3px 8px',
                    backgroundColor: 'white',
                    border: '1px solid #fda4af',
                    borderRadius: '5px',
                    color: '#be123c',
                    cursor: 'pointer'
                  }}
                  title="শুনুন"
                >
                  {isLoadingAudio && currentPlayingText?.includes(safetyMessage) ? (
                    <RefreshCw className="animate-spin" size={12} />
                  ) : isPlayingAudio && currentPlayingText?.includes(safetyMessage) ? (
                    <VolumeX size={12} />
                  ) : (
                    <Volume2 size={12} />
                  )}
                  <span>শুনুন</span>
                </button>
                <button
                  onClick={() => setIsSafetyCollapsed(false)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '3px',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#be123c',
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '3px 6px'
                  }}
                >
                  <span>বিস্তারিত</span>
                  <ChevronDown size={14} />
                </button>
              </div>
            </div>
          ) : (
            /* EXPANDED DETAILED CARD */
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={20} color="#e11d48" />
                  <h3 style={{ fontSize: '15.5px', fontWeight: '700', color: '#be123c', margin: 0 }}>
                    জরুরি নিরাপত্তা সহায়তা (হেল্পলাইন: ১৬৪৩০ / ১০৯ / ৯৯৯)
                  </h3>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={() => playVoice(safetyMessage)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      fontSize: '12px',
                      padding: '4px 10px',
                      color: '#be123c',
                      backgroundColor: 'white',
                      border: '1px solid #fda4af',
                      borderRadius: '5px',
                      cursor: 'pointer'
                    }}
                  >
                    {isLoadingAudio && currentPlayingText?.includes(safetyMessage) ? (
                      <><RefreshCw className="animate-spin" size={13} /> <span>প্রস্তুত...</span></>
                    ) : isPlayingAudio && currentPlayingText?.includes(safetyMessage) ? (
                      <><VolumeX size={13} /> <span>থামান</span></>
                    ) : (
                      <><Volume2 size={13} /> <span>শুনুন</span></>
                    )}
                  </button>
                  <button
                    onClick={() => setIsSafetyCollapsed(true)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '3px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#9f1239',
                      backgroundColor: 'white',
                      border: '1px solid #fda4af',
                      borderRadius: '5px',
                      padding: '4px 8px',
                      cursor: 'pointer'
                    }}
                    title="ব্যানার সংক্ষেপ করুন"
                  >
                    <span>সংক্ষেপ করুন</span>
                    <ChevronUp size={14} />
                  </button>
                </div>
              </div>

              <p style={{ fontSize: '13.5px', lineHeight: '1.6', color: '#881337', margin: '0 0 10px 0', whiteSpace: 'pre-line' }}>
                {safetyMessage}
              </p>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                <button 
                  onClick={() => window.open('tel:16430')}
                  style={{
                    backgroundColor: '#e11d48',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '6px 13px',
                    fontSize: '13px',
                    fontWeight: '700',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer',
                    boxShadow: '0 1px 2px rgba(225, 29, 72, 0.2)'
                  }}
                >
                  <PhoneCall size={13} /> ১৬৪৩০-এ কল করুন
                </button>
                <button 
                  onClick={() => window.open('tel:109')}
                  style={{
                    backgroundColor: 'white',
                    color: '#e11d48',
                    border: '1px solid #f43f5e',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '13px',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer'
                  }}
                >
                  <PhoneCall size={13} /> ১০৯ (নারী ও শিশু)
                </button>
                <button 
                  onClick={() => window.open('tel:999')}
                  style={{
                    backgroundColor: 'white',
                    color: '#e11d48',
                    border: '1px solid #f43f5e',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '13px',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer'
                  }}
                >
                  <PhoneCall size={13} /> ৯৯৯ (জরুরি পুলিশ)
                </button>
                <span style={{ fontSize: '12px', color: '#9f1239', fontWeight: 500, marginLeft: 'auto' }}>
                  ✓ আপনার নিরাপত্তা সবার আগে। প্রশ্নোত্তর নিচে চলমান রয়েছে।
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* FLOATING TOAST NOTIFICATION (Connection errors, 502, 401, Rate limits) */}
      {llmError && (
        <div 
          className="toast-container"
          style={{
            backgroundColor: '#ffffff',
            border: '1.5px solid #fecdd3',
            borderLeft: '5px solid #e11d48',
            borderRadius: '12px',
            boxShadow: '0 10px 25px -5px rgba(225, 29, 72, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            padding: '14px 16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <div style={{ 
              backgroundColor: '#ffe4e6', 
              color: '#e11d48', 
              borderRadius: '8px', 
              padding: '8px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {llmError.errorType === 'authentication_error' || llmError.code === 401 ? (
                <KeyRound size={20} />
              ) : llmError.errorType === 'connection_error' || llmError.code === 502 ? (
                <WifiOff size={20} />
              ) : llmError.errorType === 'permission_error' ? (
                <Mic size={20} />
              ) : llmError.errorType === 'pdf_error' ? (
                <FileText size={20} />
              ) : (
                <AlertOctagon size={20} />
              )}
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#9f1239', margin: 0 }}>
                  {llmError.title}
                </h4>
                <button
                  onClick={() => setLlmError(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    padding: '2px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="বন্ধ করুন (Dismiss)"
                >
                  <XCircle size={18} />
                </button>
              </div>

              <p style={{ fontSize: '13.5px', lineHeight: '1.5', color: '#64748b', margin: '4px 0 0' }}>
                {llmError.message}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* SCREEN: SAFETY BREAKOUT */}
      {step === 'safety' && (
        <div className="card" style={{ border: '2px solid #e11d48', backgroundColor: '#fff1f2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#e11d48' }}>
              <AlertTriangle size={32} />
              <h2 style={{ fontSize: '22px', fontWeight: '700', margin: 0 }}>জরুরি সহায়তা · BREAK-OUT</h2>
            </div>
            <button
              className="btn btn-outline"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '13px',
                padding: '6px 12px',
                borderColor: '#fda4af',
                color: '#be123c',
                backgroundColor: 'white'
              }}
              onClick={() => playVoice(safetyMessage || "আপনি এখনই বিপদে আছেন বলে মনে হচ্ছে। আপনার নিরাপত্তা সবার আগে।")}
            >
              {isLoadingAudio && currentPlayingText?.includes(safetyMessage || '') ? (
                <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
              ) : isPlayingAudio && currentPlayingText?.includes(safetyMessage || '') ? (
                <><VolumeX size={16} /> <span>থামান</span></>
              ) : (
                <><Volume2 size={16} /> <span>শুনুন</span></>
              )}
            </button>
          </div>
          <p style={{ fontSize: '16px', lineHeight: '1.7', marginBottom: '20px', color: '#881337', whiteSpace: 'pre-line' }}>
            {safetyMessage || "আপনি এখনই বিপদে আছেন বলে মনে হচ্ছে। আপনার নিরাপত্তা সবার আগে।"}
          </p>
          <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #fecdd3', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '18px', fontWeight: '700', color: '#be123c', marginBottom: '8px' }}>
              <PhoneCall size={20} />
              জাতীয় হেল্পলাইন: ১৬৪৩০ / ১০৯
            </div>
            <p style={{ fontSize: '14px', color: '#475569' }}>
              আমাদের স্বয়ংক্রিয় প্রশ্নোত্তরের পরিবর্তে আপনার অভিযোগটি জরুরি (URGENT) হিসেবে তাৎক্ষণিক প্যারালিগ্যাল ও সহায়তা টিমে পাঠানো হয়েছে।
            </p>
          </div>
          <button 
            className="btn btn-urgent" 
            style={{ width: '100%', padding: '14px', fontSize: '16px' }}
            onClick={() => window.open('tel:16430')}
          >
            এখনই কল করুন (১৬৪৩০)
          </button>
        </div>
      )}



      {/* SCREEN 1: WELCOME */}
      {step === 'welcome' && (
        <div className="card" style={{ textAlign: 'center', padding: '44px 28px' }}>
          <div style={{ width: '72px', height: '72px', borderRadius: '50%', backgroundColor: '#fef3f2', color: '#d92d20', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', boxShadow: '0 4px 14px rgba(217, 45, 32, 0.15)' }}>
            <Scale size={36} />
          </div>
          <div style={{ display: 'inline-block', backgroundColor: '#e0f2fe', color: '#0369a1', fontSize: '12px', fontWeight: '700', padding: '4px 14px', borderRadius: '20px', marginBottom: '14px' }}>
            ব্র্যাক মানবাধিকার ও আইনি সহায়তা
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: '800', marginBottom: '12px', color: '#0f172a' }}>
            অধিকার (Odhikar) — এআই প্যারালেগ্যাল
          </h1>
          <p style={{ fontSize: '16px', color: '#475569', marginBottom: '28px', lineHeight: '1.7', maxWidth: '500px', margin: '0 auto 28px' }}>
            আইনি সমস্যা নিয়ে দুশ্চিন্তা করবেন না। আপনার সাথে যা ঘটেছে, কোনো কঠিন শব্দ ছাড়াই নিজের স্বাভাবিক মুখের ভাষায় বলুন।
          </p>

          {/* 3 Trust Pillar Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '32px', textAlign: 'left' }}>
            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: '#0284c7', marginBottom: '8px' }}><Mic size={22} /></div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b' }}>ভয়েস টাইপিং</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>লিখতে না পারলে মুখে বাংলায় কথা বলুন</div>
            </div>
            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: '#16a34a', marginBottom: '8px' }}><Shield size={22} /></div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b' }}>১০০% গোপনীয়</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>আপনার পরিচয় ও বিবরণ সুরক্ষিত থাকবে</div>
            </div>
            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: '#d92d20', marginBottom: '8px' }}><HeartHandshake size={22} /></div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b' }}>বিনামূল্যে সহায়তা</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>অধিকার বিশ্লেষণ ও প্রাথমিক খসড়া</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              className="btn btn-outline"
              style={{
                padding: '12px 22px',
                fontSize: '15px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText?.includes('অধিকার। এটি একটি স্বয়ংক্রিয়') ? '#e11d48' : '#0284c7',
                color: (isPlayingAudio || isLoadingAudio) && currentPlayingText?.includes('অধিকার। এটি একটি স্বয়ংক্রিয়') ? '#e11d48' : '#0284c7'
              }}
              onClick={() => playVoice('অধিকার। এটি একটি স্বয়ংক্রিয় আইন সহায়তা সেবা — কোনো আইনজীবী নয়। আপনার আইনি সমস্যা বা ঘটনার বিবরণ নিজের ভাষায় বলুন।')}
            >
              {isLoadingAudio && currentPlayingText?.includes('অধিকার। এটি একটি স্বয়ংক্রিয়') ? (
                <><RefreshCw className="animate-spin" size={18} /> <span>প্রস্তুত হচ্ছে...</span></>
              ) : isPlayingAudio && currentPlayingText?.includes('অধিকার। এটি একটি স্বয়ংক্রিয়') ? (
                <><VolumeX size={18} /> <span>থামান</span></>
              ) : (
                <><Volume2 size={18} /> <span>নির্দেশনা শুনুন (Audio)</span></>
              )}
            </button>
            <button
              className="btn btn-primary"
              style={{ padding: '12px 32px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}
              onClick={() => {
                stopVoice();
                setStep('recording');
              }}
            >
              <span>শুরু করুন</span>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 2: INTAKE / NARRATIVE INPUT */}
      {step === 'recording' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px', color: '#0f172a' }}>
                যা ঘটেছে, নিজের ভাষায় বলুন বা লিখুন
              </h2>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
                টাইপ করতে কষ্ট হলে নীল <strong>"মুখে বলুন"</strong> বাটনে চাপ দিয়ে কথা বলুন:
              </p>
            </div>
            {renderVoiceTypingButton()}
          </div>

          {/* Voice Status Alert Box */}
          {voiceStatus && (
            <div style={{
              fontSize: '13px',
              padding: '10px 14px',
              borderRadius: '10px',
              marginBottom: '14px',
              backgroundColor: isListening ? '#fef2f2' : '#f0fdf4',
              color: isListening ? '#b91c1c' : '#15803d',
              border: `1px solid ${isListening ? '#fca5a5' : '#86efac'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              {isListening ? (
                <span className="mic-recording-pulse" style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block' }}></span>
              ) : (
                <CheckCircle2 size={16} />
              )}
              <span style={{ fontWeight: '600' }}>{voiceStatus}</span>
            </div>
          )}

          <div style={{ position: 'relative', marginBottom: '16px' }}>
            <textarea
              rows={6}
              value={textNarrative}
              onChange={(e) => setTextNarrative(e.target.value)}
              placeholder="উদাহরণ: আমার বিয়ে হয়েছে পাঁচ বছর হলো। দুই বছর ধরে স্বামী খোরপোশ দিচ্ছে না এবং কাবিনের টাকা পরিশোধ করছে না..."
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '12px',
                border: isListening ? '2px solid #0284c7' : '1px solid #cbd5e1',
                fontFamily: 'inherit',
                fontSize: '15px',
                lineHeight: '1.7',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s ease',
                boxShadow: isListening ? '0 0 0 4px rgba(2, 132, 199, 0.15)' : 'none',
                outline: 'none'
              }}
            />
            {textNarrative.trim() && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px', fontSize: '12px', color: '#64748b' }}>
                <span>শব্দ সংখ্যা: {textNarrative.trim().split(/\s+/).length} টি</span>
                <button
                  type="button"
                  onClick={() => setTextNarrative('')}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
                  title="লেখা মুছে নতুন করে বলুন"
                >
                  <Trash2 size={13} /> মুছে নতুন করে লিখুন
                </button>
              </div>
            )}
          </div>

          {/* Demo Scenario Selectors (Accessible scenario grid) */}
          <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: '700', color: '#475569', marginBottom: '10px' }}>
              <Sparkles size={15} style={{ color: '#0284c7' }} />
              <span>বা সরাসরি যেকোনো একটি নমুনা পরিস্থিতি বেছে পরীক্ষা করুন:</span>
            </div>
            <div className="scenario-grid">
              <button type="button" className="scenario-card" onClick={() => handleLoadSample('dower')}>
                <span className="scenario-title">💍 দেনমোহর ও খোরপোশ</span>
                <span className="scenario-desc">বিয়েবিচ্ছেদ ও কাবিন বকেয়া (N1)</span>
              </button>
              <button type="button" className="scenario-card" onClick={() => handleLoadSample('wages')}>
                <span className="scenario-title">💼 বকেয়া মজুরি</span>
                <span className="scenario-desc">১০ দিনের কাজের বকেয়া পাওনা (N4)</span>
              </button>
              <button type="button" className="scenario-card" style={{ borderColor: '#fca5a5' }} onClick={() => handleLoadSample('violence')}>
                <span className="scenario-title" style={{ color: '#b91c1c' }}>🚨 সহিংসতা সতর্কতা</span>
                <span className="scenario-desc">জরুরি শারীরিক নির্যাতন (N6)</span>
              </button>
              <button type="button" className="scenario-card" style={{ borderColor: '#bae6fd' }} onClick={() => handleLoadSample('long')}>
                <span className="scenario-title" style={{ color: '#0284c7' }}>📜 দীর্ঘ বিবরণ</span>
                <span className="scenario-desc">টোকেন কন্টিনিউয়েশন টেস্ট (N7)</span>
              </button>
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '14px', fontSize: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            disabled={isLoading || !textNarrative.trim()}
            onClick={() => handleSendMessage()}
          >
            {isLoading ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
            <span>{isLoading ? 'তথ্য বিশ্লেষণ করা হচ্ছে...' : 'বিবরণ জমা দিন ও বিশ্লেষণ করুন'}</span>
          </button>
        </div>
      )}

      {/* SCREEN 3: FOLLOW-UP QUESTION & CHAT HISTORY */}
      {(step === 'follow_up' || step === 'continuation') && (
        <div className="card">
          {/* Ongoing Conversation History Bubble Thread */}
          {chatHistory.length > 0 && (
            <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MessageSquare size={14} /> পূর্ববর্তী কথোপকথন ও তথ্য
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: isIntakeCompleted ? '280px' : '200px', overflowY: 'auto', paddingRight: '4px' }}>
                {chatHistory.map((msg, idx) => (
                  <div 
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}
                  >
                    <div 
                      style={{
                        backgroundColor: msg.role === 'user' ? (msg.failed ? '#fff1f2' : '#0284c7') : '#ffffff',
                        color: msg.role === 'user' ? (msg.failed ? '#9f1239' : '#ffffff') : '#1e293b',
                        border: msg.role === 'user' ? (msg.failed ? '1.5px solid #fda4af' : 'none') : '1px solid #e2e8f0',
                        boxShadow: msg.failed ? '0 1px 3px rgba(225, 29, 72, 0.1)' : '0 1px 2px rgba(0,0,0,0.04)',
                        padding: '10px 14px',
                        borderRadius: msg.role === 'user' ? '16px 16px 2px 16px' : '16px 16px 16px 2px',
                        fontSize: '14px',
                        lineHeight: '1.6',
                        maxWidth: '85%'
                      }}
                    >
                      {msg.content ? (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                          <span style={{ whiteSpace: 'pre-wrap' }}>
                            {msg.content}
                            {isStreaming && idx === chatHistory.length - 1 && msg.role === 'assistant' && (
                              <span style={{ display: 'inline-block', width: '6px', height: '14px', backgroundColor: '#0284c7', marginLeft: '4px', verticalAlign: 'middle', animation: 'pulse 1s infinite' }}></span>
                            )}
                          </span>
                          {msg.role === 'assistant' && msg.content && !isStreaming && (
                            <button
                              onClick={() => playVoice(msg.content)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                padding: '2px',
                                color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === msg.content ? '#e11d48' : '#0284c7',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title="বার্তাটি শুনুন"
                            >
                              {isLoadingAudio && currentPlayingText === msg.content ? (
                                <RefreshCw className="animate-spin" size={14} />
                              ) : isPlayingAudio && currentPlayingText === msg.content ? (
                                <VolumeX size={14} />
                              ) : (
                                <Volume2 size={14} />
                              )}
                            </button>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: '#64748b', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <RefreshCw className="animate-spin" size={14} /> {streamStatus || 'আইনি তথ্য বিশ্লেষণ করা হচ্ছে...'}
                        </span>
                      )}
                    </div>
                    {msg.role === 'user' && msg.failed && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                        <span style={{ fontSize: '12px', color: '#e11d48', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                          <AlertCircle size={13} /> বার্তাটি পাঠানো যায়নি
                        </span>
                        <button
                          onClick={() => handleRetryMessage(msg.content, idx)}
                          disabled={isLoading}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            backgroundColor: '#fee2e2',
                            border: '1px solid #fca5a5',
                            color: '#be123c',
                            borderRadius: '6px',
                            padding: '3px 9px',
                            fontSize: '12px',
                            fontWeight: '700',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                            transition: 'all 0.15s ease'
                          }}
                          title="পুনরায় চেষ্টা করুন (Retry message)"
                        >
                          <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
                          পুনরায় পাঠান
                        </button>
                      </div>
                    )}
                    {msg.role === 'assistant' && (msg.content.startsWith('⚠️ ত্রুটি:') || msg.failed) && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                        <button
                          onClick={() => handleSendMessage(lastAttemptedMessage || undefined)}
                          disabled={isLoading}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            backgroundColor: '#fee2e2',
                            border: '1px solid #fca5a5',
                            color: '#991b1b',
                            borderRadius: '6px',
                            padding: '3px 10px',
                            fontSize: '12px',
                            fontWeight: '700',
                            cursor: isLoading ? 'not-allowed' : 'pointer'
                          }}
                          title="পুনরায় চেষ্টা করুন"
                        >
                          <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
                          পুনরায় চেষ্টা করুন (Retry)
                        </button>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            </div>
          )}

          {/* Active Question Highlight Box OR Completion Notification */}
          {isIntakeCompleted ? (
            isOutOfScope ? (
              <div style={{
                backgroundColor: '#fffbeb',
                border: '1.5px solid #fcd34d',
                borderRadius: '14px',
                padding: '18px',
                marginBottom: '18px',
                boxShadow: '0 2px 8px rgba(245, 158, 11, 0.08)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertTriangle size={20} color="#d97706" />
                    <span style={{ fontSize: '14px', fontWeight: '800', color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      আইনি সেবার আওতাভুক্ত নয় (Out of Scope)
                    </span>
                  </div>
                  {rightsExplanation && (
                    <button
                      type="button"
                      className="btn btn-outline"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px',
                        padding: '4px 10px',
                        backgroundColor: 'white',
                        borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#d97706',
                        color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#b45309'
                      }}
                      onClick={() => playVoice(rightsExplanation)}
                      title="পরামর্শ শুনুন"
                    >
                      {isLoadingAudio && currentPlayingText === rightsExplanation ? (
                        <><RefreshCw className="animate-spin" size={14} /> <span>প্রস্তুত হচ্ছে...</span></>
                      ) : isPlayingAudio && currentPlayingText === rightsExplanation ? (
                        <><VolumeX size={14} /> <span>থামান</span></>
                      ) : (
                        <><Volume2 size={14} /> <span>পরামর্শ শুনুন</span></>
                      )}
                    </button>
                  )}
                </div>

                <p style={{ margin: '0 0 16px 0', fontSize: '14.5px', color: '#78350f', lineHeight: '1.7', whiteSpace: 'pre-line' }}>
                  {rightsExplanation || 'আপনার বিষয়টি আমাদের এই মুহূর্তের বিনামূল্যে পারিবারিক ও শ্রম আইনি সহায়তার আওতাভুক্ত নয়। তবে এ বিষয়ে আপনি সাধারণ ডায়েরি (GD) বা থানা এবং নিকটস্থ সরকারি লিগ্যাল এইড অফিসে যোগাযোগ করতে পারেন। প্রয়োজনে জাতীয় হেল্পলাইন ৩৩৩ বা ৯৯৯-এ যোগাযোগ করুন।'}
                </p>

                {/* Relevant Emergency & Legal Helplines for Out-of-Scope Issues */}
                <div style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #fde68a',
                  borderRadius: '10px',
                  padding: '14px',
                  marginBottom: '16px'
                }}>
                  <div style={{ fontSize: '12.5px', fontWeight: '700', color: '#92400e', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <PhoneCall size={14} /> জরুরি সহায়তা ও জাতীয় হেল্পলাইন নম্বর:
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                    <a
                      href="tel:999"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 12px',
                        backgroundColor: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: '#991b1b',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      <Shield size={18} color="#dc2626" />
                      <div>
                        <div>৯৯৯ (জাতীয় জরুরি সেবা)</div>
                        <div style={{ fontSize: '11px', color: '#7f1d1d', fontWeight: 'normal' }}>পুলিশ, ফায়ার সার্ভিস ও অ্যাম্বুলেন্স</div>
                      </div>
                    </a>

                    <a
                      href="tel:16430"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 12px',
                        backgroundColor: '#eff6ff',
                        border: '1px solid #bfdbfe',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: '#1e40af',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      <Scale size={18} color="#2563eb" />
                      <div>
                        <div>১৬৪৩০ (আইনি সহায়তা)</div>
                        <div style={{ fontSize: '11px', color: '#1e3a8a', fontWeight: 'normal' }}>সরকারি জাতীয় লিগ্যাল এইড কলসেন্টার</div>
                      </div>
                    </a>

                    <a
                      href="tel:333"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 12px',
                        backgroundColor: '#f0fdf4',
                        border: '1px solid #bbf7d0',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: '#166534',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      <PhoneCall size={18} color="#16a34a" />
                      <div>
                        <div>৩৩৩ (সরকারি সেবা কলসেন্টার)</div>
                        <div style={{ fontSize: '11px', color: '#14532d', fontWeight: 'normal' }}>সরকারি সেবা ও পরামর্শ</div>
                      </div>
                    </a>

                    <a
                      href="tel:109"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 12px',
                        backgroundColor: '#faf5ff',
                        border: '1px solid #e9d5ff',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: '#6b21a8',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      <HeartHandshake size={18} color="#9333ea" />
                      <div>
                        <div>১০৯ (নারী ও শিশু নির্যাতন)</div>
                        <div style={{ fontSize: '11px', color: '#581c87', fontWeight: 'normal' }}>সহায়তা ও প্রতিরোধ হেল্পলাইন</div>
                      </div>
                    </a>
                  </div>
                </div>

                {/* Reset / Start New Intake Button */}
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      backgroundColor: '#d97706',
                      borderColor: '#b45309',
                      padding: '10px 20px',
                      fontSize: '14px',
                      fontWeight: '700',
                      borderRadius: '8px',
                      boxShadow: '0 2px 6px rgba(217, 119, 6, 0.25)',
                      cursor: 'pointer'
                    }}
                    onClick={handleStartNewCase}
                  >
                    <RefreshCw size={15} />
                    <span>নতুন আরেকটি আইনি আবেদন শুরু করুন</span>
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ backgroundColor: '#f0fdf4', border: '1.5px solid #86efac', borderRadius: '12px', padding: '16px', marginBottom: '18px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <CheckCircle2 size={18} color="#16a34a" />
                  <span style={{ fontSize: '13px', fontWeight: '800', color: '#15803d', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    প্রশ্নোত্তর পর্ব সম্পন্ন হয়েছে
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '14.5px', color: '#166534', lineHeight: '1.6' }}>
                  আপনার বিবরণ ও সকল প্রশ্নের উত্তর সফলভাবে সংরক্ষিত হয়েছে। এখন আপনার এলাকা অনুযায়ী <strong>নিকটস্থ ব্র্যাক লিগ্যাল এইড ক্লিনিক</strong> খুঁজে বের করতে এবং আপনার নামে সঠিক <strong>অভিযোগপত্র (Draft Complaint)</strong> তৈরি করতে নিচের ব্যক্তিগত ও বিবাদীর তথ্য দিন:
                </p>
              </div>
            )
          ) : continuationPrompt ? (
            <div style={{
              backgroundColor: '#f0f9ff',
              border: '2px solid #0284c7',
              borderRadius: '14px',
              padding: '18px',
              marginBottom: '18px',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.08)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0284c7' }}>
                  <ArrowRightCircle size={22} />
                  <span style={{ fontSize: '15px', fontWeight: '700' }}>টোকেন ও বিস্তারিত বিশ্লেষণ সম্মতি</span>
                </div>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    padding: '4px 10px',
                    backgroundColor: 'white',
                    borderColor: '#bae6fd',
                    color: '#0284c7'
                  }}
                  onClick={() => playVoice(continuationPrompt)}
                >
                  {isLoadingAudio && currentPlayingText === continuationPrompt ? (
                    <><RefreshCw className="animate-spin" size={14} /> <span>প্রস্তুত হচ্ছে...</span></>
                  ) : isPlayingAudio && currentPlayingText === continuationPrompt ? (
                    <><VolumeX size={14} /> <span>থামান</span></>
                  ) : (
                    <><Volume2 size={14} /> <span>শুনুন</span></>
                  )}
                </button>
              </div>

              <p style={{ fontSize: '14px', lineHeight: '1.7', marginBottom: '14px', color: '#0c4a6e' }}>
                {continuationPrompt}
              </p>

              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #bae6fd',
                borderRadius: '8px',
                padding: '10px 12px',
                marginBottom: '14px',
                fontSize: '12.5px',
                color: '#0369a1',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Sparkles size={16} color="#0284c7" style={{ flexShrink: 0 }} />
                <span>
                  <strong>এআই সারসংক্ষেপ সুবিধা:</strong> মূল আইনি তথ্য (দেনমোহর, তারিখ, বকেয়া, বিবাদী) অক্ষুণ্ণ রেখে অতিরিক্ত টোকেন খরচ এড়াতে এআই বক্তব্যটি সংক্ষেপ করে সাথে সাথে বিশ্লেষণ সম্পন্ন করতে পারে।
                </span>
              </div>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{
                    flex: '1.5 1 220px',
                    backgroundColor: '#0284c7',
                    borderColor: '#0284c7',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    fontSize: '14px',
                    padding: '11px 16px',
                    fontWeight: '600'
                  }}
                  disabled={isLoading || isSummarizing}
                  onClick={handleSummarizeAndContinue}
                >
                  {isSummarizing ? (
                    <><RefreshCw className="animate-spin" size={16} /> <span>এআই দিয়ে সংক্ষেপ করা হচ্ছে...</span></>
                  ) : (
                    <><Sparkles size={16} /> <span>✨ এআই দিয়ে সংক্ষেপ করে এগিয়ে যান</span></>
                  )}
                </button>

                <button
                  type="button"
                  className="btn btn-outline"
                  style={{
                    flex: '1 1 140px',
                    backgroundColor: 'white',
                    borderColor: '#cbd5e1',
                    color: '#475569',
                    fontSize: '13.5px',
                    padding: '11px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    fontWeight: '600'
                  }}
                  disabled={isLoading || isSummarizing}
                  onClick={handleEditNarrative}
                >
                  <Edit3 size={15} /> <span>নিজে এডিট করুন</span>
                </button>
              </div>
            </div>
          ) : followUpQuestion && !isStreaming && !isLoading ? (
            <div style={{ backgroundColor: '#f0f9ff', border: '1.5px solid #bae6fd', borderRadius: '12px', padding: '16px', marginBottom: '18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  আইনি পরামর্শের জন্য প্রয়োজনীয় প্রশ্ন:
                </span>
                <button
                  className="btn btn-outline"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    padding: '4px 10px',
                    flexShrink: 0,
                    backgroundColor: 'white',
                    borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText === followUpQuestion ? '#e11d48' : '#0284c7',
                    color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === followUpQuestion ? '#e11d48' : '#0284c7'
                  }}
                  onClick={() => playVoice(followUpQuestion)}
                  title="প্রশ্নটি শুনুন"
                >
                  {isLoadingAudio && currentPlayingText === followUpQuestion ? (
                    <><RefreshCw className="animate-spin" size={14} /> <span>প্রস্তুত হচ্ছে...</span></>
                  ) : isPlayingAudio && currentPlayingText === followUpQuestion ? (
                    <><VolumeX size={14} /> <span>থামান</span></>
                  ) : (
                    <><Volume2 size={14} /> <span>প্রশ্ন শুনুন</span></>
                  )}
                </button>
              </div>
              <h2 style={{ fontSize: '17px', fontWeight: '700', color: '#0c4a6e', margin: 0, lineHeight: '1.6' }}>
                {followUpQuestion}
              </h2>
            </div>
          ) : null}

          {/* VOICE-FIRST PROFILE & AGGRESSOR DETAILS ASSISTANT (Right Before Step 4) */}
          {isIntakeCompleted && !isOutOfScope && (
            <div style={{
              backgroundColor: '#ffffff',
              border: '2px solid #0284c7',
              borderRadius: '14px',
              padding: '20px',
              marginBottom: '20px',
              boxShadow: '0 6px 18px rgba(2, 132, 199, 0.08)'
            }}>
              {/* Header with audio prompt */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0369a1', fontWeight: '700', fontSize: '16px' }}>
                  <Mic size={20} color="#0284c7" />
                  <span>মুখে বলুন — এআই স্বয়ংক্রিয়ভাবে ফর্ম পূরণ করে নেবে</span>
                </div>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    padding: '4px 10px',
                    backgroundColor: 'white',
                    borderColor: '#0284c7',
                    color: '#0284c7'
                  }}
                  onClick={() => playVoice('আপনার এবং প্রতিপক্ষের নাম ও এলাকার ঠিকানা মুখে বলুন। এআই কথা শুনে স্বয়ংক্রিয়ভাবে তথ্য পূরণ করে নেবে।')}
                  title="নির্দেশনাটি শুনুন"
                >
                  <Volume2 size={14} /> <span>নির্দেশনা শুনুন</span>
                </button>
              </div>

              <p style={{ fontSize: '13px', color: '#475569', marginBottom: '14px', lineHeight: '1.5' }}>
                কোনো ফর্ম টাইপ করার প্রয়োজন নেই! নিচে <strong>'মুখে বলুন'</strong> চেপে আপনার নাম, বাবার নাম, এলাকা (উপজেলা, জেলা) এবং বিবাদীর নাম ও সম্পর্ক স্বাভাবিক বাংলায় বলুন। কৃত্রিম বুদ্ধিমত্তা স্বয়ংক্রিয়ভাবে তথ্য শনাক্ত করে নিকটস্থ ব্র্যাক কেন্দ্র খুঁজে নেবে।
              </p>

              {/* Voice Recording Control & Status */}
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '12px' }}>
                <button
                  type="button"
                  onClick={isListeningProfile ? stopProfileVoiceTyping : startProfileVoiceTyping}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 18px',
                    borderRadius: '10px',
                    fontSize: '14px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    backgroundColor: isListeningProfile ? '#ef4444' : '#0284c7',
                    color: 'white',
                    border: 'none',
                    boxShadow: isListeningProfile ? '0 0 12px rgba(239, 68, 68, 0.4)' : '0 2px 8px rgba(2, 132, 199, 0.25)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {isListeningProfile ? (
                    <>
                      <Square size={16} fill="white" />
                      <span>কথা বলা শেষ হলে থামান</span>
                    </>
                  ) : (
                    <>
                      <Mic size={18} />
                      <span>মুখে বলুন (ট্যাপ করে কথা বলুন)</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleSampleVoiceProfile}
                  disabled={isExtractingProfile || isListeningProfile}
                  style={{
                    fontSize: '12.5px',
                    color: '#0284c7',
                    background: '#f0f9ff',
                    border: '1px solid #bae6fd',
                    borderRadius: '8px',
                    padding: '8px 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                  title="নমুনা কণ্ঠস্বর দিয়ে এআই অটো-ফিলিং পরীক্ষা করুন"
                >
                  <Sparkles size={14} /> <span>নমুনা কণ্ঠস্বর দিয়ে পরীক্ষা</span>
                </button>
              </div>

              {/* Spoken Text Area (Auto populated via speech recognition or user edit) */}
              <div style={{ marginBottom: '12px' }}>
                <textarea
                  rows={2}
                  value={profileVoiceTranscript}
                  onChange={(e) => setProfileVoiceTranscript(e.target.value)}
                  placeholder="মুখে বললে এখানে সরাসরি লেখা উঠবে... (যেমন: আমার নাম রহিমা খাতুন, বাড়ি কুমিল্লার চান্দিনায় বাতাঘাসী গ্রামে। স্বামী রফিকুল ইসলাম চান্দিনা বাজারে থাকে।)"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: isListeningProfile ? '2px solid #ef4444' : '1px solid #cbd5e1',
                    fontSize: '13.5px',
                    fontFamily: 'inherit',
                    boxSizing: 'border-box',
                    backgroundColor: isListeningProfile ? '#fef2f2' : '#f8fafc',
                    lineHeight: '1.5'
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                  <span style={{ fontSize: '11.5px', color: '#64748b' }}>
                    {isListeningProfile ? '🔴 আপনার কথা শুনছি... কথা বলা শেষ হলে "থামান" চাপুন।' : 'কথা বলা শেষে এআই সরাসরি আপনার নাম ও ঠিকানা শনাক্ত করবে।'}
                  </span>
                  {profileVoiceTranscript.trim() && (
                    <button
                      type="button"
                      onClick={() => handleExtractProfileVoice()}
                      disabled={isExtractingProfile}
                      style={{
                        fontSize: '12px',
                        color: '#047857',
                        background: '#ecfdf5',
                        border: '1px solid #a7f3d0',
                        borderRadius: '6px',
                        padding: '4px 10px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontWeight: '600'
                      }}
                    >
                      {isExtractingProfile ? <RefreshCw className="animate-spin" size={12} /> : <CheckCircle2 size={12} />}
                      <span>{isExtractingProfile ? 'শনাক্ত হচ্ছে...' : 'পুনরায় তথ্য শনাক্ত করুন'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* AI EXTRACTED SUMMARY BADGE CARD */}
              {(hasVoiceExtracted || applicantName || (thana && zilla)) && (
                <div style={{
                  backgroundColor: '#f0fdf4',
                  border: '1.5px solid #86efac',
                  borderRadius: '10px',
                  padding: '14px',
                  marginBottom: '14px',
                  boxShadow: '0 2px 8px rgba(22, 163, 74, 0.05)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: '700', color: '#166534', fontSize: '13.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} color="#16a34a" /> কণ্ঠস্বর থেকে স্বয়ংক্রিয় শনাক্তকৃত তথ্য:
                    </span>
                    <span style={{ fontSize: '11px', backgroundColor: '#dcfce7', color: '#15803d', padding: '2px 8px', borderRadius: '12px', fontWeight: '600' }}>
                      এআই দ্বারা প্রস্তুত
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '13px', color: '#1e293b' }}>
                    <div>
                      <span style={{ color: '#64748b' }}>আবেদনকারী: </span>
                      <strong>{isAnonymous ? '[নাম গোপন রাখা হয়েছে]' : (applicantName || '[নাম সংরক্ষিত]')}</strong>
                      {fatherName ? ` (পিতা: ${fatherName})` : ''}
                      {contactNumber ? ` | 📞 ${contactNumber}` : ''}
                    </div>

                    <div>
                      <span style={{ color: '#64748b' }}>এলাকা: </span>
                      <strong>{[unionVillage, thana, zilla].filter(Boolean).join(', ')} ({division})</strong>
                    </div>

                    <div>
                      <span style={{ color: '#64748b' }}>প্রতিপক্ষ: </span>
                      <strong>{aggressorName || '[বিবাদী]'}</strong> ({aggressorRelation})
                      {aggressorAddress ? ` — ${aggressorAddress}` : ''}
                    </div>
                  </div>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#475569', marginTop: '10px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={isAnonymous}
                      onChange={(e) => setIsAnonymous(e.target.checked)}
                    />
                    <span>নাম গোপন রাখতে চান? (অভিযোগপত্রে [নাম সংরক্ষিত] থাকবে)</span>
                  </label>
                </div>
              )}

              {/* Optional Manual Form Toggle */}
              <div style={{ borderTop: '1px dashed #cbd5e1', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => setShowManualForm(!showManualForm)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12.5px',
                    color: '#0369a1',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '4px 0',
                    fontWeight: '600'
                  }}
                >
                  <Edit3 size={14} />
                  <span>{showManualForm ? 'ফর্মটি বন্ধ করুন' : 'প্রয়োজনে কোনো তথ্য টাইপ বা এডিট করতে চান? (ফর্ম খুলুন)'}</span>
                  {showManualForm ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                <button
                  type="button"
                  onClick={handleQuickFillProfile}
                  style={{
                    fontSize: '11.5px',
                    color: '#64748b',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  ডেমো ভ্যালু রিসেট
                </button>
              </div>

              {/* DETAILED MANUAL FORM (Shown only if user expands it) */}
              {showManualForm && (
                <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid #e2e8f0' }}>
                  {/* Applicant Name & Father's Name */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        আপনার পূর্ণ নাম:
                      </label>
                      <input
                        type="text"
                        value={applicantName}
                        onChange={(e) => setApplicantName(e.target.value)}
                        disabled={isAnonymous}
                        placeholder={isAnonymous ? "[নাম গোপন থাকবে]" : "যেমন: মোসাম্মৎ রহিমা খাতুন"}
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        পিতার নাম (ঐচ্ছিক):
                      </label>
                      <input
                        type="text"
                        value={fatherName}
                        onChange={(e) => setFatherName(e.target.value)}
                        placeholder="যেমন: মোঃ করিম মিয়া"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>
                  </div>

                  {/* Location: Division, Zilla, Thana */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        বিভাগ (Division): *
                      </label>
                      <select
                        value={division}
                        onChange={(e) => {
                          const newDiv = e.target.value;
                          setDivision(newDiv);
                          const dists = BANGLADESH_DIVISIONS[newDiv] || [];
                          if (dists.length > 0) setZilla(dists[0]);
                        }}
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', backgroundColor: 'white', boxSizing: 'border-box' }}
                      >
                        {Object.keys(BANGLADESH_DIVISIONS).map((divName) => (
                          <option key={divName} value={divName}>{divName}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        জেলা (Zilla / District): *
                      </label>
                      <select
                        value={zilla}
                        onChange={(e) => setZilla(e.target.value)}
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', backgroundColor: 'white', boxSizing: 'border-box' }}
                      >
                        {(BANGLADESH_DIVISIONS[division] || []).map((distName) => (
                          <option key={distName} value={distName}>{distName}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        উপজেলা / থানা (Thana / Upazila): *
                      </label>
                      <input
                        type="text"
                        value={thana}
                        onChange={(e) => setThana(e.target.value)}
                        placeholder="যেমন: চান্দিনা / মিরপুর / সাভার"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>
                  </div>

                  {/* Location: Union & Phone */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        ইউনিয়ন / গ্রাম / ওয়ার্ড:
                      </label>
                      <input
                        type="text"
                        value={unionVillage}
                        onChange={(e) => setUnionVillage(e.target.value)}
                        placeholder="যেমন: বাতাঘাসী ইউনিয়ন"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        মোবাইল নম্বর (ঐচ্ছিক):
                      </label>
                      <input
                        type="text"
                        value={contactNumber}
                        onChange={(e) => setContactNumber(e.target.value)}
                        placeholder="যেমন: ০১৭১২-৩৪৫৬৭৮"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>
                  </div>

                  {/* Section 2: Aggressor Information */}
                  <div style={{ borderTop: '1px dashed #cbd5e1', paddingTop: '12px', marginTop: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#b91c1c', fontWeight: '700', fontSize: '14px', marginBottom: '10px' }}>
                      <Shield size={16} />
                      <span>প্রতিপক্ষ / বিবাদীর তথ্য:</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '10px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                          বিবাদী / প্রতিপক্ষের নাম:
                        </label>
                        <input
                          type="text"
                          value={aggressorName}
                          onChange={(e) => setAggressorName(e.target.value)}
                          placeholder="যেমন: মোঃ রফিকুল ইসলাম"
                          style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                        />
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                          আপনার সাথে সম্পর্ক:
                        </label>
                        <select
                          value={aggressorRelation}
                          onChange={(e) => setAggressorRelation(e.target.value)}
                          style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', backgroundColor: 'white', boxSizing: 'border-box' }}
                        >
                          <option value="স্বামী">স্বামী</option>
                          <option value="শ্বশুর / শাশুড়ি / শ্বশুরবাড়ির লোক">শ্বশুর / শাশুড়ি / শ্বশুরবাড়ির লোক</option>
                          <option value="প্রতিবেশী">প্রতিবেশী</option>
                          <option value="জমির দখলদার / শরিক">জমির দখলদার / শরিক</option>
                          <option value="মালিক / ঠিকাদার">মালিক / ঠিকাদার</option>
                          <option value="অন্যান্য">অন্যান্য</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                        বিবাদীর বর্তমান এলাকা বা ঠিকানা:
                      </label>
                      <input
                        type="text"
                        value={aggressorAddress}
                        onChange={(e) => setAggressorAddress(e.target.value)}
                        placeholder="যেমন: চান্দিনা বাজার, কুমিল্লা"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13.5px', boxSizing: 'border-box' }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {!isIntakeCompleted && (
            <>
              {/* Answer Input Header with Voice Typing Button */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#334155' }}>আপনার উত্তর:</span>
                {renderVoiceTypingButton()}
              </div>

              {voiceStatus && (
                <div style={{
                  fontSize: '12px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  marginBottom: '10px',
                  backgroundColor: isListening ? '#fef2f2' : '#f0fdf4',
                  color: isListening ? '#b91c1c' : '#15803d',
                  border: `1px solid ${isListening ? '#fca5a5' : '#86efac'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  {isListening ? (
                    <span className="mic-recording-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block' }}></span>
                  ) : (
                    <CheckCircle2 size={14} />
                  )}
                  <span>{voiceStatus}</span>
                </div>
              )}

              <textarea
                rows={3}
                value={textNarrative}
                onChange={(e) => setTextNarrative(e.target.value)}
                placeholder="উত্তর মুখে বলুন বা এখানে লিখুন... (কথা বললে সরাসরি লেখা হবে)"
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '10px',
                  border: isListening ? '2px solid #0284c7' : '1px solid #cbd5e1',
                  fontFamily: 'inherit',
                  fontSize: '15px',
                  marginBottom: '12px',
                  boxSizing: 'border-box',
                  outline: 'none',
                  lineHeight: '1.6'
                }}
              />

              {/* Quick Answer Shortcut Chips */}
              {(() => {
                const isGenerating = isLoading || isStreaming;
                if (isGenerating) return null;

                const activeQuestion = followUpQuestion || 
                  (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'assistant' 
                     ? chatHistory[chatHistory.length - 1].content 
                     : '');
                const chips = getContextualChips(activeQuestion, suggestedReplies, sessionState?.category);
                if (!chips || chips.length === 0) return null;

                return (
                  <div className="quick-chips-wrapper">
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'flex', alignItems: 'center', marginRight: '4px' }}>
                      সহায়ক উত্তর:
                    </span>
                    {chips.map((chip, idx) => {
                      const isSelected = textNarrative === chip.text;
                      return (
                        <button
                          key={idx}
                          type="button"
                          className={`quick-chip ${isSelected ? 'active' : ''}`}
                          onClick={() => setTextNarrative(chip.text)}
                          title={chip.text}
                        >
                          {chip.label}
                        </button>
                      );
                    })}
                  </div>
                );
              })()}
            </>
          )}

          {/* Action Button: Changes to 'Confirm Profile & View Step 4' when questionnaires are completed */}
          <div style={{ marginTop: '14px' }}>
            {isIntakeCompleted ? (
              !isOutOfScope ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <button
                    className="btn btn-primary"
                    disabled={isFinalizingProfile}
                    style={{
                      width: '100%',
                      padding: '14px 24px',
                      fontSize: '16px',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '10px',
                      backgroundColor: '#16a34a',
                      borderColor: '#15803d',
                      boxShadow: '0 4px 14px rgba(22, 163, 74, 0.25)',
                      borderRadius: '10px',
                      cursor: isFinalizingProfile ? 'not-allowed' : 'pointer'
                    }}
                    onClick={handleFinalizeProfile}
                  >
                    {isFinalizingProfile ? (
                      <>
                        <RefreshCw className="animate-spin" size={18} />
                        <span>নিকটস্থ ব্র্যাক কেন্দ্র ও অভিযোগপত্র প্রস্তুত হচ্ছে...</span>
                      </>
                    ) : (
                      <>
                        <span>নিকটস্থ ব্র্যাক কেন্দ্র ও অভিযোগপত্র দেখুন (ধাপ ৪)</span>
                        <ChevronRight size={20} />
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      stopVoice();
                      setStep('referral');
                    }}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#64748b',
                      fontSize: '13px',
                      cursor: 'pointer',
                      padding: '6px',
                      textDecoration: 'underline'
                    }}
                  >
                    তথ্য পূরণ ছাড়াই সরাসরি এগিয়ে যান (Skip to Step 4)
                  </button>
                </div>
              ) : null
            ) : (
              <button
                className="btn btn-primary"
                style={{ width: '100%', padding: '13px', fontSize: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                disabled={isLoading || isStreaming || !textNarrative.trim()}
                onClick={() => {
                  stopVoice();
                  handleSendMessage();
                }}
              >
                {isLoading || isStreaming ? <RefreshCw className="animate-spin" size={18} /> : <Send size={16} />}
                <span>{isLoading || isStreaming ? 'তথ্য তৈরি হচ্ছে...' : 'উত্তর জমা দিন'}</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* SCREEN 4: YOUR RIGHTS (Commented out per user request) */}
      {/*
      {step === 'rights' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '18px' }}>
            <div style={{ backgroundColor: '#e0f2fe', color: '#0284c7', padding: '10px', borderRadius: '12px' }}>
              <Scale size={26} />
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase' }}>আইনি পথ ও সমাধান</div>
              <h2 style={{ fontSize: '22px', fontWeight: '800', margin: 0, color: '#0f172a' }}>আপনার আইনগত অধিকার</h2>
            </div>
          </div>

          {rightsExplanation && (
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-outline"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  padding: '7px 16px',
                  borderRadius: '20px',
                  borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#0284c7',
                  color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#0284c7'
                }}
                onClick={() => playVoice(rightsExplanation)}
              >
                {isLoadingAudio && currentPlayingText === rightsExplanation ? (
                  <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
                ) : isPlayingAudio && currentPlayingText === rightsExplanation ? (
                  <><VolumeX size={16} /> <span>থামান</span></>
                ) : (
                  <><Volume2 size={16} /> <span>পরামর্শ শুনুন (Audio)</span></>
                )}
              </button>
            </div>
          )}

          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
            <p style={{ fontSize: '15px', lineHeight: '1.8', whiteSpace: 'pre-line', color: '#334155', margin: 0 }}>
              {rightsExplanation}
            </p>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <button 
              className="btn btn-outline" 
              style={{ padding: '12px 20px', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }} 
              onClick={() => { stopVoice(); setStep('follow_up'); }}
            >
              <span>← পূর্ববর্তী প্রশ্নোত্তর দেখুন</span>
            </button>
            <button className="btn btn-primary" style={{ padding: '12px 28px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => { stopVoice(); setStep('referral'); }}>
              <span>ক্লিনিক ও আবেদনের খসড়া দেখুন</span> <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
      */}

      {/* SCREEN 5: REFERRAL & DRAFT COMPLAINT */}
      {step === 'referral' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <div style={{ backgroundColor: '#dcfce7', color: '#16a34a', padding: '10px', borderRadius: '12px' }}>
              <CheckCircle2 size={26} />
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#16a34a', textTransform: 'uppercase' }}>মামলা আইডি #{caseId || 'NEW'}</div>
              <h2 style={{ fontSize: '22px', fontWeight: '800', margin: 0, color: '#0f172a' }}>নিকটস্থ আইন সহায়তা কেন্দ্র</h2>
            </div>
          </div>

          {/* Referral Appointment Card */}
          <div style={{ backgroundColor: '#f0fdf4', border: '1.5px solid #86efac', padding: '20px', borderRadius: '14px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(22, 163, 74, 0.08)' }}>
            <div style={{ fontWeight: '800', fontSize: '18px', color: '#14532d', marginBottom: '6px' }}>
              {referralInfo?.clinic}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '15px', color: '#166534', fontWeight: '600', marginBottom: '10px' }}>
              <Check size={16} />
              <span>নির্ধারিত সাক্ষাত: {referralInfo?.slot}</span>
            </div>
            <p style={{ fontSize: '13px', color: '#475569', lineHeight: '1.6', margin: '0 0 14px' }}>
              আপনার তথ্যের ভিত্তিতে প্রাথমিক অভিযোগের খসড়া প্রস্তুত করা হয়েছে এবং ব্র্যাক প্যারালিগ্যাল ড্যাশবোর্ডে ফরোয়ার্ড করা হয়েছে।
            </p>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-outline"
                style={{ backgroundColor: 'white', borderColor: '#86efac', color: '#15803d', fontSize: '13px', padding: '7px 14px' }}
                onClick={() => playVoice(`আপনার নিকটতম আইন সহায়তা কেন্দ্র ${referralInfo?.clinic || ''}। নির্ধারিত সাক্ষাৎ ${referralInfo?.slot || ''}।`)}
              >
                <Volume2 size={15} /> ঠিকানা শুনুন
              </button>
              <a
                href="tel:16430"
                className="btn btn-primary"
                style={{ backgroundColor: '#16a34a', fontSize: '13px', padding: '7px 16px', textDecoration: 'none' }}
              >
                <PhoneCall size={15} /> হেল্পলাইনে কল দিন (১৬৪৩০)
              </a>
            </div>
          </div>

          {/* Draft Complaint Preview */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#1e293b', margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileText size={18} color="#d92d20" />
              <span>প্রাথমিক অভিযোগের খসড়া (Draft First Complaint):</span>
            </h3>
            {draftComplaint && (
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={handleDownloadDraftPdf}
                  disabled={isDownloadingPdf}
                  style={{
                    backgroundColor: '#d92d20',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '6px 14px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: isDownloadingPdf ? 'wait' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 2px 4px rgba(217, 45, 32, 0.25)',
                    transition: 'all 0.2s'
                  }}
                  title="অফিসিয়াল ফরম্যাটে অভিযোগপত্রের খসড়া PDF ডাউনলোড করুন"
                >
                  {isDownloadingPdf ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Download size={13} />}
                  <span>{isDownloadingPdf ? 'পিডিএফ তৈরি হচ্ছে...' : 'PDF ডাউনলোড'}</span>
                </button>

                <button
                  onClick={handlePrintDraft}
                  style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: '#334155'
                  }}
                  title="প্রিন্ট প্রিভিউ দেখুন অথবা প্রিন্ট করুন"
                >
                  <Printer size={13} />
                  <span>প্রিন্ট</span>
                </button>

                <button
                  onClick={() => handleCopyDraft(draftComplaint)}
                  style={{
                    background: 'none',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: copiedDraft ? '#16a34a' : '#475569'
                  }}
                  title="খসড়ার টেক্সট ক্লিপবোর্ডে কপি করুন"
                >
                  {copiedDraft ? <Check size={13} /> : <Copy size={13} />}
                  <span>{copiedDraft ? 'কপি হয়েছে!' : 'খসড়া কপি'}</span>
                </button>
              </div>
            )}
          </div>
          <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '13px', whiteSpace: 'pre-line', color: '#334155', maxHeight: '220px', overflowY: 'auto', marginBottom: '24px', lineHeight: '1.7', fontFamily: 'monospace' }}>
            {draftComplaint}
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button 
              type="button"
              className="btn btn-outline" 
              style={{ flex: 1, padding: '13px', fontSize: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }} 
              onClick={() => { stopVoice(); setStep('follow_up'); }}
            >
              <span>← পূর্ববর্তী প্রশ্নোত্তর ও তথ্য দেখুন</span>
            </button>
            <button 
              type="button"
              className="btn btn-primary" 
              style={{ flex: 1.5, padding: '13px', fontSize: '15px' }}
              onClick={handleStartNewCase}
            >
              নতুন আরেকটি আবেদন শুরু করুন
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
