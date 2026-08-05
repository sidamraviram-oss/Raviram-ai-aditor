const express = require('express');
const fileUpload = require('express-fileupload');
const qrcode = require('qrcode');
const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload());

const ADMIN_SECRET_KEY = "raviram0536";
const SECURE_PHONE_NUMBER = "9502981109";
const SECURE_UPI_ID = `${SECURE_PHONE_NUMBER}@paytm`;
const OWNER_NAME = "Film Maker & Editor";

const ADMIN_EMAIL = "raviram@ai.com";
const ADMIN_PASS = "raviram0536";

function validateAndSanitizeInput(text) {
    if (!text) return "";
    
    const forbiddenPatterns = [/</, />/, /\//, /script/i, /javascript:/i, /SELECT/i, /DROP/i];
    
    for (let pattern of forbiddenPatterns) {
        if (pattern.test(text)) {
            throw new Error(`Security Alert: Invalid characters or code detected ('${pattern}'). Request blocked!`);
        }
    }
    return text;
}

async function saveToGoogleSheet(dataDict) {
    try {
        const auth = new JWT({
            email: "your-service-account-email@...com",
            key: "your-private-key",
            scopes: ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
        });

        const doc = new GoogleSpreadsheet("AI_Video_Generator_Logs", auth);
        await doc.loadInfo();
        const sheet = doc.sheetsByIndex[0];

        await sheet.addRow([
            dataDict.timestamp,
            dataDict.user_email,
            dataDict.role,
            dataDict.project_type,
            dataDict.uploaded_image,
            dataDict.uploaded_audio,
            dataDict.uploaded_video,
            dataDict.bg_effect,
            dataDict.lighting_effect,
            dataDict.voice_effect,
            String(dataDict.video_duration_minutes),
            String(dataDict.total_amount),
            String(dataDict.status)
        ]);
    } catch (e) {
        console.log("Google Sheet Error:", e.message);
    }
}

function calculateAmount(minutes) {
    if (minutes <= 1) return 59.0;
    else if (minutes <= 3) return 149.0;
    else if (minutes <= 5) return 299.0;
    else if (minutes <= 10) return 599.0;
    else return parseFloat(minutes * 60);
}

app.get("/", (req, res) => {
    res.json({
        welcome: `Welcome to ${OWNER_NAME}'s Official Platform & AI Video Generator!`,
        pricing_list: [
            { duration: "1 Minute", price: "₹59" },
            { duration: "3 Minutes", price: "₹149" },
            { duration: "5 Minutes", price: "₹299" },
            { duration: "10 Minutes", price: "₹599" }
        ]
    });
});

app.post("/edit-and-generate-video/", async (req, res) => {
    try {
        let project_type = validateAndSanitizeInput(req.body.project_type || "Short Film");
        let bg_effect = validateAndSanitizeInput(req.body.bg_effect || "Cinematic Background");
        let lighting_effect = validateAndSanitizeInput(req.body.lighting_effect || "Dramatic Lighting");
        let voice_effect = validateAndSanitizeInput(req.body.voice_effect || "Studio Quality Voice");
        let user_email = validateAndSanitizeInput(req.body.user_email || "guest@gmail.com");
        
        let video_minutes = parseInt(req.body.video_minutes || 3);
        let secret_key = req.body.secret_key;

        let currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

        let imageName = "No Image";
        if (req.files && req.files.file) {
            imageName = req.files.file.name;
            req.files.file.mv(`./uploads/${imageName}`);
        }

        let audioName = "No Audio";
        if (req.files && req.files.audio_file) {
            audioName = req.files.audio_file.name;
            req.files.audio_file.mv(`./audio_uploads/${audioName}`);
        }

        let videoName = "No Video";
        if (req.files && req.files.raw_video) {
            videoName = req.files.raw_video.name;
            req.files.raw_video.mv(`./video_uploads/${videoName}`);
        }

        let amount = calculateAmount(video_minutes);

        if (secret_key === ADMIN_SECRET_KEY || user_email === ADMIN_EMAIL) {
            let role = "Boss (Admin)";
            let status = "Success (Free Access)";

            let logData = {
                timestamp: currentTime, user_email: user_email, role: role, project_type: project_type,
                uploaded_image: imageName, uploaded_audio: audioName, uploaded_video: videoName,
                bg_effect: bg_effect, lighting_effect: lighting_effect, voice_effect: voice_effect,
                video_duration_minutes: video_minutes, total_amount: 0.0, status: status
            };
            await saveToGoogleSheet(logData);

            return res.json({
                status: "Success",
                role: role,
                message: `Welcome Boss (${user_email})! Free access granted securely.`,
                payment_required: false,
                final_edited_video: "https://ai-video-generator.local/secure_output.mp4"
            });
        }

        let upiPayLink = `upi://pay?pa=${SECURE_UPI_ID}&pn=${encodeURIComponent(OWNER_NAME)}&am=${amount}&cu=INR`;
        let qrCodeDataUrl = await qrcode.toDataURL(upiPayLink);

        let status = "Payment Required";
        let role = "Regular User";

        let logData = {
            timestamp: currentTime, user_email: user_email, role: role, project_type: project_type,
            uploaded_image: imageName, uploaded_audio: audioName, uploaded_video: videoName,
            bg_effect: bg_effect, lighting_effect: lighting_effect, voice_effect: voice_effect,
            video_duration_minutes: video_minutes, total_amount: amount, status: status
        };
        await saveToGoogleSheet(logData);

        return res.json({
            status: status,
            role: role,
            message: `Please pay ₹${amount} to process your video, ${user_email}.`,
            payment_required: true,
            payment_details: {
                total_amount: amount,
                upi_intent_link: upiPayLink,
                qr_code_scanner: qrCodeDataUrl
            },
            final_edited_video: null
        });

    } catch (e) {
        return res.status(400).json({ status: "Error", message: e.message });
    }
});

app.listen(3000, () => {
    console.log("Server is running securely on port 3000");
});
