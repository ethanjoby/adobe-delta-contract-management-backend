const { Document, Packer, Paragraph, TextRun } = require('docx');
const fs = require('fs');

// Number to words conversion (handles 1-20, adjust as needed)
const numberToWords = {
    1: "One (1)",
    2: "One (1) / Two (2)",
    3: "One (1) / Two (2) / Three (3)",
    4: "One (1) / Two (2) / Three (3) / Four (4)",
    5: "One (1) / Two (2) / Three (3) / Four (4) / Five (5)",
    6: "One (1) / Two (2) / Three (3) / Four (4) / Five (5) / Six (6)",
    7: "One (1) / Two (2) / Three (3) / Four (4) / Five (5) / Six (6) / Seven (7)",
    8: "One (1) / Two (2) / Three (3) / Four (4) / Five (5) / Six (6) / Seven (7) / Eight (8)",
    9: "One (1) / Two (2) / Three (3) / Four (4) / Five (5) / Six (6) / Seven (7) / Eight (8) / Nine (9)",
    10: "One (1) / Two (2) / Three (3) / Four (4) / Five (5) / Six (6) / Seven (7) / Eight (8) / Nine (9) / Ten (10)"
};

function convertNumberToWords(num) {
    const number = parseInt(num);
    return numberToWords[number] || `${number}`;
}

function generateRegularContract(data) {
    const numText = data.number_of_content ? convertNumberToWords(data.number_of_content) : "one (1)";
    
    return [
        new Paragraph({ children: [new TextRun({ text: `Artist/vendor name: ${data.contractor_name}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Name of person signing the contract (if not the artist/vendor): ${data.signer_name}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Relationship to artist/vendor: ${data.relationship_to_vendor}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Address: ${data.address}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Email address: ${data.email}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Vendor account: ${data.vendor_account}`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Summary:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Vendor will create and provide to Adobe ${numText} video(s) with content to promote select Adobe products.`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Deliverables:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ 
            text: `Vendor will provide Adobe with ${numText} pre-recorded video(s) that will be between 30 seconds and one minute in length that highlight Adobe products. Specific details, including Adobe product(s), will be selected by Adobe in writing. For each video, Vendor will (1) orally disclose the relationship between Vendor and Adobe and (2) include a clearly visible written overlay disclosing the relationship. Unless otherwise specified by Adobe in writing, each video's aspect ratio will be 9:16.`,
            break: 1
        })] }),
        new Paragraph({ children: [new TextRun({
            text: `Vendor will post the video(s) on various social media channels owned and controlled by the Vendor, which the parties will agree to in writing. [The video(s) must be authenticated via the CreatorIQ website for analytic purposes, with a 30-day Ad code for all video created on applicable social media platforms provided to Adobe to track performance.]`,
            break: 2
        })] }),
        new Paragraph({ children: [new TextRun({
            text: `For clarity, Adobe shall have the right to like, favorite, share, repost, redistribute, syndicate, amplify (paid promotion or allow listing) or otherwise use all video described hereunder in any manner enabled by the applicable platform. Adobe can use the video and may redistribute to other Adobe owned accounts, channels, and/or platforms. Vendor will allow 1 round of edits per video.`,
            break: 2
        })] }),
        new Paragraph({ children: [new TextRun({
            text: `In the event that all pre-recorded video(s) are not delivered, Adobe will pay a pro-rated rate for content delivered in accordance with this Agreement.`,
            break: 2
        })] }),
        new Paragraph({ children: [new TextRun({
            text: `Beginning on the Effective Date, and concluding thirty (30) days after Vendor's publication of the video(s) with Adobe's authorization, Vendor will not provide services on behalf of, appear or participate in any advertising, publicity or promotion of, endorse, or authorize or permit the use of Vendor's Likeness in connection with the following (the "Restricted Category"): (a) any software and online creative development and cloud service companies (for clarity, the Restricted Category includes, without limitation, Spline, Womp, Canva, Affinity, CapCut, Autodesk, DaVinci, Final Cut Pro, Figma, Procreate, Capture One Pro); or (b) any product or service that in its advertising or publicity denigrates Adobe or its products. For clarity, the aforementioned does not preclude Vendor from merely appearing in any entertainment portion of any news, TV, or film program or attending an event, regardless of sponsorship.`,
            break: 2
        })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Delivery Schedule:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Unless otherwise directed in writing by Adobe, ${data.due_date}`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: `Price and currency: $${data.amount} USD`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `End Date: ${data.end_date}`, break: 1 })] }),
    ];
}

function generateCampfireContract(data) {
    const numText = data.number_of_content ? convertNumberToWords(data.number_of_content) : "one (1)";
    
    return [
        new Paragraph({ children: [new TextRun({ text: `Artist/vendor name: ${data.contractor_name}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Name of person signing the contract (if not the artist/vendor): ${data.signer_name}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Relationship to artist/vendor: ${data.relationship_to_vendor}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Address: ${data.address}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Email address: ${data.email}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Vendor account: ${data.vendor_account}`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Summary:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Vendor will create and provide to Adobe ${numText} video(s) with content to promote select Adobe products.`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Deliverables:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ 
            text: `Vendor will provide Adobe with ${numText} pre-recorded video(s) that will be between 30 seconds and one minute in length that highlight Adobe products. Specific details, including Adobe product(s), will be selected by Adobe in writing. For each video, Vendor will (1) orally disclose the relationship between Vendor and Adobe and (2) include a clearly visible written overlay disclosing the relationship. Unless otherwise specified by Adobe in writing, each video's aspect ratio will be 9:16.`,
            break: 1
        })] }),
        new Paragraph({ children: [new TextRun({
            text: `Vendor will post the video(s) on various social media channels owned and controlled by the Vendor, which the parties will agree to in writing. The video(s) must include a 30-day Ad code for all video created on applicable social media platforms provided to Adobe.`,
            break: 2
        })] }),
        
        new Paragraph({ children: [new TextRun({ text: "Delivery Schedule:", bold: true, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `Unless otherwise directed in writing by Adobe, ${data.due_date}`, break: 2 })] }),
        
        new Paragraph({ children: [new TextRun({ text: `Price and currency: $${data.amount}`, break: 1 })] }),
        new Paragraph({ children: [new TextRun({ text: `End Date: ${data.end_date}`, break: 1 })] }),
    ];
}

function generateContract(data, outputPath) {
    const isCampfire = data.contract_type === 'campfire';
    const content = isCampfire ? generateCampfireContract(data) : generateRegularContract(data);
    
    const doc = new Document({
        styles: {
            default: {
                document: {
                    run: { font: "Arial", size: 24 } // 12pt
                }
            }
        },
        sections: [{
            properties: {
                page: {
                    size: {
                        width: 12240,   // 8.5 inches (US Letter)
                        height: 15840   // 11 inches
                    },
                    margin: {
                        top: 1440,      // 1 inch
                        right: 1440,
                        bottom: 1440,
                        left: 1440
                    }
                }
            },
            children: content
        }]
    });
    
    return Packer.toBuffer(doc).then(buffer => {
        fs.writeFileSync(outputPath, buffer);
        return outputPath;
    });
}

// Export for use in Python via subprocess
if (require.main === module) {
    const data = JSON.parse(process.argv[2]);
    const outputPath = process.argv[3];
    
    generateContract(data, outputPath)
        .then(() => {
            console.log(`Contract generated: ${outputPath}`);
            process.exit(0);
        })
        .catch(err => {
            console.error(`Error: ${err.message}`);
            process.exit(1);
        });
}

module.exports = { generateContract };
