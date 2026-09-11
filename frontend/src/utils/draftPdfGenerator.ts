import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export interface DraftPdfOptions {
  draftText: string;
  caseId?: string | number | null;
  category?: string | null;
  categoryBangla?: string | null;
  applicantName?: string | null;
  respondent?: string | null;
  address?: string | null;
  clinicName?: string | null;
  appointmentSlot?: string | null;
  date?: string | null;
  status?: string | null;
}

const formatPlaceholders = (text: string): string => {
  if (!text) return '';
  // Convert newlines to HTML breaks
  // Highlight brackets placeholders like [অপ্রতিষ্ঠিত], [নাম], [বিবাদীর নাম], etc.
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const highlighted = escaped.replace(/(\[[^\]]+\])/g, '<span class="pdf-placeholder">$1</span>');
  return highlighted.replace(/\n/g, '<br/>');
};

const getCategoryLabel = (cat?: string | null, catBn?: string | null): string => {
  if (catBn) return catBn;
  if (!cat) return 'পারিবারিক — দেনমোহর ও ভরণপোষণ';
  const map: Record<string, string> = {
    'family_dower_maintenance': 'পারিবারিক — দেনমোহর ও ভরণপোষণ',
    'dowry': 'যৌতুক সংক্রান্ত বিরোধ ও নির্যাতন',
    'unpaid_wages': 'শ্রম ও কর্মসংস্থান — বকেয়া মজুরি আদায়',
    'land_dispute': 'ভূমি ও সম্পত্তি সংক্রান্ত বিরোধ',
    'out_of_scope': 'অন্যান্য / সাধারণ আইনি বিষয়'
  };
  return map[cat] || cat;
};

const buildDocumentHtml = (options: DraftPdfOptions): string => {
  const caseIdDisplay = options.caseId ? `ODH-2026-${String(options.caseId).padStart(4, '0')}` : 'ODH-2026-DRAFT';
  const currentDate = options.date || new Date().toLocaleDateString('bn-BD', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }) || new Date().toLocaleDateString();
  const categoryLabel = getCategoryLabel(options.category, options.categoryBangla);
  const applicant = options.applicantName || '[নাম সংরক্ষিত]';
  const respondent = options.respondent || '[বিবাদী]';
  const address = options.address || '[ঠিকানা — অপ্রতিষ্ঠিত]';
  const clinic = options.clinicName || 'ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র';
  const slot = options.appointmentSlot || 'বুধবার, সকাল ১০:০০ টা';
  const statusLabel = options.status === 'URGENT' ? 'জরুরি অগ্রাধিকার (URGENT)' : 'প্রাথমিক খসড়া (Draft Prepared)';
  const formattedBody = formatPlaceholders(options.draftText);

  return `
    <div id="odhikar-pdf-template" style="
      width: 794px;
      min-height: 1120px;
      padding: 44px 50px 40px 50px;
      box-sizing: border-box;
      background-color: #ffffff;
      color: #0f172a;
      font-family: 'Hind Siliguri', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      position: relative;
      line-height: 1.6;
    ">
      <style>
        .pdf-placeholder {
          background-color: #fef3c7;
          color: #92400e;
          border: 1px dashed #d97706;
          border-radius: 3px;
          padding: 1px 5px;
          font-weight: 600;
          font-size: 0.95em;
        }
      </style>

      <!-- TOP OFFICIAL HEADER -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #d92d20; padding-bottom: 14px; margin-bottom: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <div style="background-color: #d92d20; color: #ffffff; font-weight: 800; font-size: 18px; padding: 2px 10px; border-radius: 4px; letter-spacing: 0.5px;">
              অধিকার · ODHIKAR
            </div>
            <span style="font-size: 13px; color: #64748b; font-weight: 600;">
              AI Paralegal for Legal Aid Clients
            </span>
          </div>
          <div style="font-size: 15px; font-weight: 700; color: #1e293b;">
            ব্র্যাক মানবাধিকার ও আইনি সহায়তা কর্মসূচি (HRLS)
          </div>
          <div style="font-size: 12px; color: #475569;">
            BRAC Human Rights and Legal Aid Services · Legal Intake & Case Preparation
          </div>
        </div>

        <div style="text-align: right;">
          <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 12px; display: inline-block;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase;">ট্র্যাকিং নম্বর (Case ID)</div>
            <div style="font-size: 14px; font-weight: 800; color: #0f172a; font-family: monospace;">${caseIdDisplay}</div>
          </div>
          <div style="font-size: 11px; color: #64748b; margin-top: 5px;">
            প্রস্তুতের তারিখ: <strong>${currentDate}</strong>
          </div>
        </div>
      </div>

      <!-- WATERMARK & LEGAL NOTICE BANNER -->
      <div style="
        background-color: #fef2f2;
        border: 1.5px solid #f87171;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 18px;
        display: flex;
        align-items: flex-start;
        gap: 10px;
      ">
        <div style="font-size: 20px; line-height: 1;">⚠️</div>
        <div style="font-size: 11.5px; color: #991b1b; line-height: 1.45;">
          <strong style="font-size: 12.5px;">খসড়া কপি — প্যারালিগ্যাল পর্যালোচনা ও অনুমোদন ব্যতীত আদালতে বা সরকারি দপ্তরে ব্যবহারযোগ্য নয়:</strong><br/>
          এই নথিটি অধিকার এআই কর্তৃক ক্লায়েন্টের প্রাথমিক বর্ণনার ভিত্তিতে প্রস্তুতকৃত একটি অনানুষ্ঠানিক খসড়া অভিযোগপত্র। ব্র্যাক লিগ্যাল এইড ক্লিনিকের নিয়োগপ্রাপ্ত প্যারালিগ্যাল কর্মকর্তা কর্তৃক তথ্য যাচাই, সংযোজন এবং স্বাক্ষরের পূর্বে এটি কোনো চূড়ান্ত আইনি দলিল বলে গণ্য হবে না।
        </div>
      </div>

      <!-- DOCUMENT TITLE -->
      <div style="text-align: center; margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.2px;">
          আইনি বিরোধ মীমাংসার অভিযোগপত্র (প্রাথমিক খসড়া)
        </h1>
        <div style="font-size: 12px; color: #475569; margin-top: 3px;">
          বিষয়শ্রেণি: <strong>${categoryLabel}</strong> · অবস্থা: <span style="color: ${options.status === 'URGENT' ? '#e11d48' : '#0284c7'}; font-weight: 700;">${statusLabel}</span>
        </div>
      </div>

      <!-- CASE METADATA TABLE -->
      <div style="
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: #f8fafc;
        padding: 12px 16px;
        margin-bottom: 20px;
        font-size: 12px;
      ">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px;">
          <div>
            <span style="color: #64748b; font-weight: 600;">অভিযোগকারী (Applicant):</span>
            <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin-top: 1px;">${applicant}</div>
          </div>
          <div>
            <span style="color: #64748b; font-weight: 600;">বিবাদী / অপরপক্ষ (Respondent):</span>
            <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin-top: 1px;">${respondent}</div>
          </div>
          <div>
            <span style="color: #64748b; font-weight: 600;">অভিযোগকারীর ঠিকানা:</span>
            <div style="color: #334155; margin-top: 1px;">${address}</div>
          </div>
          <div>
            <span style="color: #64748b; font-weight: 600;">রেফার্ড লিগ্যাল এইড ক্লিনিক:</span>
            <div style="color: #334155; font-weight: 600; margin-top: 1px;">${clinic} (${slot})</div>
          </div>
        </div>
      </div>

      <!-- FORMAL DRAFT COMPLAINT TEXT -->
      <div style="
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background-color: #ffffff;
        padding: 22px 24px;
        margin-bottom: 24px;
        min-height: 420px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
      ">
        <div style="
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 700;
          color: #64748b;
          border-bottom: 1px solid #f1f5f9;
          padding-bottom: 8px;
          margin-bottom: 16px;
        ">
          আবেদনের মূল বক্তব্য ও খসড়া পত্র (Reviewed Template Complaint Body)
        </div>
        <div style="
          font-size: 13.5px;
          line-height: 1.85;
          color: #1e293b;
          white-space: normal;
          text-align: justify;
        ">
          ${formattedBody}
        </div>
      </div>

      <!-- VERIFICATION & SIGNATURE BLOCK -->
      <div style="
        border-top: 1.5px dashed #94a3b8;
        padding-top: 16px;
        margin-top: 24px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 30px;
      ">
        <!-- Applicant signature -->
        <div style="display: flex; flex-direction: column; justify-content: space-between; height: 110px;">
          <div style="font-size: 11px; color: #475569; line-height: 1.4;">
            <strong>অভিযোগকারীর অঙ্গীকার:</strong><br/>
            উপরে উল্লেখিত সকল তথ্য আমার বর্ণিত বিবরণ অনুযায়ী সংরক্ষিত হইয়াছে।
          </div>
          <div>
            <div style="border-bottom: 1px solid #0f172a; width: 180px; margin-bottom: 4px;"></div>
            <div style="font-size: 11.5px; font-weight: 700; color: #1e293b;">
              অভিযোগকারী / প্রতিনিধির স্বাক্ষর বা টিপসহি
            </div>
            <div style="font-size: 10px; color: #64748b;">তারিখ: .......................................</div>
          </div>
        </div>

        <!-- Paralegal review signature -->
        <div style="display: flex; flex-direction: column; justify-content: space-between; height: 110px; text-align: right;">
          <div style="font-size: 11px; color: #475569; line-height: 1.4;">
            <strong>প্যারালিগ্যাল কর্মকর্তা যাচাই ও সুপারিশ:</strong><br/>
            খসড়াটি ক্লায়েন্টের উপস্থিতিতে যাচাইকৃত এবং সালিশি/পরামর্শের জন্য প্রস্তুত।
          </div>
          <div style="display: flex; flex-direction: column; align-items: flex-end;">
            <div style="border-bottom: 1px solid #0f172a; width: 220px; margin-bottom: 4px;"></div>
            <div style="font-size: 11.5px; font-weight: 700; color: #1e293b;">
              দায়িত্বপ্রাপ্ত প্যারালিগ্যাল কর্মকর্তার স্বাক্ষর ও সিল
            </div>
            <div style="font-size: 10px; color: #64748b;">
              আইন সহায়তা কেন্দ্র, ব্র্যাক · তারিখ: ........................
            </div>
          </div>
        </div>
      </div>

      <!-- FOOTER -->
      <div style="
        position: absolute;
        bottom: 24px;
        left: 50px;
        right: 50px;
        border-top: 1px solid #e2e8f0;
        padding-top: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 10px;
        color: #94a3b8;
      ">
        <div>
          অধিকার (Odhikar) AI Paralegal · ব্র্যাক আইটি কোডস্প্রিন্ট ২০২৬ | জাতীয় হেল্পলাইন: <strong>১৬৪৩০</strong> | জরুরি পুলিশ: <strong>৯৯৯</strong>
        </div>
        <div>
          পৃষ্ঠা ১ / ১ (Page 1 of 1)
        </div>
      </div>
    </div>
  `;
};

/**
 * Generates and downloads a clean, professional PDF file of the draft complaint.
 */
export const downloadDraftPdf = async (options: DraftPdfOptions): Promise<void> => {
  if (!options.draftText || !options.draftText.trim()) {
    throw new Error('খসড়া অভিযোগপত্রের কোনো তথ্য পাওয়া যায়নি।');
  }

  // Create temporary container off-screen
  const container = document.createElement('div');
  container.style.position = 'fixed';
  container.style.left = '-9999px';
  container.style.top = '0';
  container.style.zIndex = '-9999';
  container.style.width = '794px';
  container.innerHTML = buildDocumentHtml(options);
  document.body.appendChild(container);

  try {
    const targetElement = container.firstElementChild as HTMLElement;
    if (!targetElement) {
      throw new Error('টেমপ্লেট রেন্ডারিং ব্যর্থ হয়েছে।');
    }

    // Wait a moment for fonts and layout to settle
    await new Promise((resolve) => setTimeout(resolve, 150));

    // Render HTML to canvas with high resolution scale 2
    const canvas = await html2canvas(targetElement, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      windowWidth: 794
    });

    const imgData = canvas.toDataURL('image/jpeg', 0.95);
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress: true
    });

    const imgWidth = 210; // A4 width in mm
    const pageHeight = 297; // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    let heightLeft = imgHeight;
    let position = 0;

    // First page
    pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
    heightLeft -= pageHeight;

    // Additional pages if text is long
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
      heightLeft -= pageHeight;
    }

    const safeId = options.caseId ? String(options.caseId).replace(/[^a-zA-Z0-9_-]/g, '') : 'new';
    const fileName = `Odhikar_Draft_Complaint_${safeId}.pdf`;
    pdf.save(fileName);
  } finally {
    if (container.parentNode) {
      container.parentNode.removeChild(container);
    }
  }
};

/**
 * Prints the draft complaint using the browser's native print engine (supports Save to PDF).
 */
export const printDraftPdf = (options: DraftPdfOptions): void => {
  if (!options.draftText || !options.draftText.trim()) {
    alert('খসড়া অভিযোগপত্রের কোনো তথ্য পাওয়া যায়নি।');
    return;
  }

  const printWindow = window.open('', '_blank', 'width=900,height=800');
  if (!printWindow) {
    alert('পপ-আপ উইন্ডো খুলতে পারছে না। দয়া করে ব্রাউজারের পপ-আপ অনুমতি দিন।');
    return;
  }

  const htmlContent = `
    <!DOCTYPE html>
    <html lang="bn">
      <head>
        <meta charset="utf-8" />
        <title>Draft Complaint — Odhikar</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
          @page {
            size: A4 portrait;
            margin: 12mm 15mm 12mm 15mm;
          }
          body {
            margin: 0;
            padding: 0;
            background: #ffffff;
            font-family: 'Hind Siliguri', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          @media print {
            body {
              width: 100%;
            }
          }
        </style>
      </head>
      <body>
        ${buildDocumentHtml(options)}
        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
            }, 350);
          };
        </script>
      </body>
    </html>
  `;

  printWindow.document.open();
  printWindow.document.write(htmlContent);
  printWindow.document.close();
};
