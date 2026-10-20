// Is this a scam? -- the scenarios for Game.html ("Scam or Safe?").
//
// Each round of the game shows one of these messages. Edit or add scenarios
// here; js/game.js only draws them. Every company and person is made up
// (SwiftPost, MyBank, GameVault, ZoomCart, TouchPay, StudyHub, Clipr, Aina).
//
// FIELDS
//   id         a short unique name
//   answer     "scam" or "safe"
//   channel    how it arrives: "sms", "email", "chat", "call" or "web"
//   situation  what is going on in your life when it arrives (it matters!)
//   ...        the message itself, depending on the channel (see below)
//   clues      what to notice, numbered. For a scam these are red flags; for a
//              safe message they are the signs that it is real.
//   hint       a nudge shown if the player asks for one
//   takeaway   the one thing to remember
//   learn      the part of Learn.html that explains it ("#links", "#baits", ...)
//
// MARKING CLUES
//   In any message text, [[2|some words]] marks "some words" as clue number 2.
//   The marks are hidden while the player decides, and shown with the answer.
//   The text is put on screen as text, never as HTML.
//
// CHANNELS
//   sms    from, text
//   email  fromName, fromAddress, subject, body (paragraphs), button, linkTarget
//   chat   app, contact, contactNote, messages
//   call   caller, label, lines ({who, text})
//   web    url, title, body (paragraphs), fields, button

window.GAME_SCENARIOS = [
  // --- Scams --------------------------------------------------------------------
  {
    id: "parcel-fee",
    answer: "scam",
    channel: "sms",
    situation: "You ordered earphones online last week and you're waiting for them.",
    from: "[[4|+60 11-1234 5678]]",
    text: "SwiftPost: Your parcel could not be delivered due to an incomplete address. [[1|Pay RM1.99]] to reschedule [[2|within 12 hours]] or it will be returned: [[3|swiftpost-redelivery.top/my]]",
    clues: [
      { n: 1, title: "A tiny fee", text: "Couriers don't ask you to pay through a link in a text. The small amount is bait to get your card details." },
      { n: 2, title: "A countdown", text: "\"Within 12 hours\" is there to rush you." },
      { n: 3, title: "Not the courier's website", text: "The owner of this link is swiftpost-redelivery.top, not SwiftPost." },
      { n: 4, title: "A personal mobile number", text: "A courier writes from its own name or short code, not from a random mobile number." }
    ],
    hint: "Would a real courier ask you to pay by tapping a link in a text?",
    takeaway: "Waiting for a parcel is exactly when this scam works. Check the tracking number in the courier's own app.",
    learn: "#baits"
  },
  {
    id: "bank-verify",
    answer: "scam",
    channel: "email",
    situation: "You have a MyBank account.",
    fromName: "MyBank Security",
    fromAddress: "[[1|security@mybank-alerts.help]]",
    subject: "[[2|URGENT]]: Unusual sign-in detected",
    body: [
      "[[3|Dear Customer]],",
      "We detected a sign-in to your account from a new device. If this wasn't you, your account will be [[2|suspended within 24 hours]].",
      "To keep your account, verify your identity now and [[4|enter the TAC code we send you]]."
    ],
    button: "Verify now",
    linkTarget: "http://[[5|mybank-secure-verify.com]]/login",
    clues: [
      { n: 1, title: "Wrong sender", text: "MyBank's address ends in mybank.com.my. This one is \"mybank-alerts.help\"." },
      { n: 2, title: "Rush and threat", text: "\"URGENT\" and \"suspended within 24 hours\" are there to make you panic." },
      { n: 3, title: "\"Dear Customer\"", text: "Your bank knows your name." },
      { n: 4, title: "Asks for your TAC", text: "No bank ever asks you to type your TAC or OTP after following a link." },
      { n: 5, title: "Fake link", text: "The owner of this link is mybank-secure-verify.com, not MyBank." }
    ],
    hint: "Look at who sent it, and where the button really goes.",
    takeaway: "If a bank message worries you, close it and open the bank's app yourself, or call the number on your card.",
    learn: "#flags"
  },
  {
    id: "friend-otp",
    answer: "scam",
    channel: "chat",
    situation: "You have a friend called Aina.",
    app: "Messages",
    contact: "[[1|+60 12-1234 5678]]",
    contactNote: "[[1|Not in your contacts]]",
    messages: [
      "Hi! It's Aina, [[2|this is my new number]] 😅",
      "I accidentally sent a [[3|6-digit code]] to your phone, can you send it to me? [[4|Quick pls, it expires soon!]]"
    ],
    clues: [
      { n: 1, title: "Unknown number", text: "It isn't Aina's saved number, so you can't be sure it's her." },
      { n: 2, title: "\"New number\" story", text: "A classic opener. Check with Aina on her old number or in person." },
      { n: 3, title: "Asks for a code", text: "That code unlocks YOUR account (chat app, e-wallet, bank). Whoever has it can get in." },
      { n: 4, title: "Rush", text: "\"Quick pls\" leaves you no time to check." }
    ],
    hint: "What could someone do with a code that was sent to YOUR phone?",
    takeaway: "Never share a one-time code with anyone, even a \"friend\". Check with them another way.",
    learn: "#baits"
  },
  {
    id: "game-diamonds",
    answer: "scam",
    channel: "chat",
    situation: "You're playing GameVault and a player sends you a message.",
    app: "GameVault chat",
    contact: "[[1|GV_Admin_Official]]",
    contactNote: "[[1|Player · Level 3]]",
    messages: [
      "🎉 [[2|Congrats! You've been picked for 10,000 FREE diamonds!]]",
      "Log in with your GameVault account at [[3|gamevault-gift.xyz]] to claim. [[4|Only 50 spots left!]]"
    ],
    clues: [
      { n: 1, title: "A fake admin", text: "Anyone can call themselves \"Admin_Official\". This is a level 3 player, not staff." },
      { n: 2, title: "Too good to be true", text: "10,000 free diamonds, just for you, out of nowhere." },
      { n: 3, title: "Log in somewhere else", text: "A website that isn't the game wants your game login. That's how accounts get stolen." },
      { n: 4, title: "Hurry", text: "\"Only 50 spots left\" is there to rush you." }
    ],
    hint: "Where do real game rewards appear?",
    takeaway: "Real rewards appear inside the game. Never log in to your game account on another website.",
    learn: "#baits"
  },
  {
    id: "job-deposit",
    answer: "scam",
    channel: "chat",
    situation: "You haven't applied for any job.",
    app: "Messages",
    contact: "[[1|Recruiter Mira]]",
    contactNote: "[[1|Not in your contacts]]",
    messages: [
      "Hi! We saw your profile. [[2|Earn RM300 a day]] just liking videos at home, no experience needed 💰",
      "To start, [[3|pay a RM50 registration deposit]] to our account. [[4|Limited spots for students!]]"
    ],
    clues: [
      { n: 1, title: "Out of nowhere", text: "A stranger, and you never applied." },
      { n: 2, title: "Too-easy money", text: "RM300 a day for liking videos is not a real job." },
      { n: 3, title: "Pay to work", text: "A real job pays you. It never asks you to pay first." },
      { n: 4, title: "Hurry", text: "\"Limited spots\" is there to rush you." }
    ],
    hint: "Who should be paying whom in a real job?",
    takeaway: "If a job asks you to pay before you earn, it's a scam.",
    learn: "#baits"
  },
  {
    id: "police-call",
    answer: "scam",
    channel: "call",
    situation: "Your phone rings after school.",
    caller: "[[1|Unknown number]]",
    label: "Incoming call",
    lines: [
      { who: "Caller", text: "Hello, this is [[2|Inspector Lim from the police]]. Your bank account has been [[3|linked to a money laundering case]]." },
      { who: "Caller", text: "To clear your name, you must [[4|move your money to a safe account]] that we give you. [[5|Don't tell your family]], this is a secret investigation." }
    ],
    clues: [
      { n: 1, title: "Unknown caller", text: "You can't see who is really calling." },
      { n: 2, title: "Authority", text: "Claiming to be police makes you want to obey without thinking." },
      { n: 3, title: "Fear", text: "A scary accusation stops you from thinking clearly." },
      { n: 4, title: "Move your money", text: "Police and banks never ask you to transfer money to a \"safe account\"." },
      { n: 5, title: "Keep it secret", text: "Secrecy stops a parent or friend from warning you." }
    ],
    hint: "Would real police ask you to move money and keep it from your family?",
    takeaway: "Hang up. Tell a parent, then call the police or the National Scam Response Centre on 997 yourself.",
    learn: "#why"
  },
  {
    id: "qr-credit",
    answer: "scam",
    channel: "web",
    situation: "You scan a QR sticker on a café table that says \"Scan for RM10 free e-wallet credit!\"",
    url: "[[1|touchpay-rewards.net]]/claim",
    title: "TouchPay: Claim your RM10",
    body: [
      "[[2|Enter your phone number and 6-digit e-wallet PIN]] to receive your free credit.",
      "[[3|Offer ends in 04:59]]"
    ],
    fields: ["Phone number", "[[2|E-wallet PIN]]"],
    button: "Claim RM10",
    clues: [
      { n: 1, title: "Not the e-wallet's website", text: "The owner is touchpay-rewards.net, not TouchPay." },
      { n: 2, title: "Asks for your PIN", text: "Your PIN is the key to your money. No real offer needs it." },
      { n: 3, title: "A timer", text: "The countdown is there to rush you." }
    ],
    hint: "A QR code is just a link. Read the address it opened.",
    takeaway: "After scanning a QR code, check the address before typing anything, and never give your PIN.",
    learn: "#links"
  },
  {
    id: "popup-virus",
    answer: "scam",
    channel: "web",
    situation: "You're reading a website and this suddenly covers the screen.",
    url: "[[1|phone-security-check.click]]/alert",
    title: "⚠️ Warning!",
    body: [
      "[[2|Your phone has 3 viruses!]] Your photos and accounts are at risk.",
      "[[3|Install CleanBoost within 60 seconds]] to remove them."
    ],
    button: "Install now",
    clues: [
      { n: 1, title: "A random website", text: "Not your phone's settings or a security app you installed." },
      { n: 2, title: "Fake scare", text: "A website can't scan your phone for viruses." },
      { n: 3, title: "Install, quickly", text: "A timer plus \"install this app\" is how harmful apps get onto phones." }
    ],
    hint: "Can a web page really see inside your phone?",
    takeaway: "Close the tab. Never install an app because a pop-up told you to.",
    learn: "#why"
  },
  {
    id: "scholarship-fee",
    answer: "scam",
    channel: "email",
    situation: "You never applied for a scholarship.",
    fromName: "StudyHub Scholarship",
    fromAddress: "[[1|studyhub.scholarship2026@gmail.com]]",
    subject: "Congratulations! Your scholarship is approved 🎓",
    body: [
      "Dear Student,",
      "[[2|You have been awarded a RM2,000 scholarship!]]",
      "To release the money, [[3|pay a RM30 processing fee]] [[4|by Friday]] to the account below."
    ],
    clues: [
      { n: 1, title: "A free email account", text: "Schools write from their own address, not a free gmail.com account." },
      { n: 2, title: "Too good to be true", text: "A prize for something you never applied for." },
      { n: 3, title: "Pay to receive", text: "If you must pay money to get money, it's a scam." },
      { n: 4, title: "Deadline", text: "\"By Friday\" is there to rush you." }
    ],
    hint: "Did you apply? And why would you pay to receive money?",
    takeaway: "Paying a fee to receive money is always a scam. Ask your school directly.",
    learn: "#baits"
  },
  {
    id: "refund-lookalike",
    answer: "scam",
    channel: "email",
    situation: "You bought something on ZoomCart last month.",
    fromName: "ZoomCart Refunds",
    fromAddress: "refunds@[[1|zoomcart-refund.com]]",
    subject: "Your refund of RM89.00 is waiting",
    body: [
      "[[2|Hi customer]],",
      "Your recent order was cancelled. [[3|To get your RM89.00 refund, enter your card number and CVV]] on our refund page."
    ],
    button: "Get my refund",
    linkTarget: "https://zoomcart.com.my.[[4|refund-centre.co]]/claim",
    clues: [
      { n: 1, title: "Not the shop's address", text: "ZoomCart writes from zoomcart.com.my, not \"zoomcart-refund.com\"." },
      { n: 2, title: "\"Hi customer\"", text: "The shop knows your name from your order." },
      { n: 3, title: "Card number and CVV", text: "Refunds go back to your card by themselves. Nobody needs your CVV to give you money." },
      { n: 4, title: "Brand in the wrong place", text: "The link starts with zoomcart.com.my, but its real owner is refund-centre.co." }
    ],
    hint: "Read the link carefully. Who really owns it?",
    takeaway: "Refunds come back on their own. Never type card details to \"receive\" money.",
    learn: "#links"
  },
  {
    id: "clipr-copyright",
    answer: "scam",
    channel: "chat",
    situation: "You post videos on Clipr, a video app.",
    app: "Clipr messages",
    contact: "[[1|Clipr Support Team ✔]]",
    contactNote: "[[1|0 followers · joined this week]]",
    messages: [
      "Your video [[2|broke copyright rules]]. Your account will be [[3|deleted in 24 hours]].",
      "Appeal here to keep it: [[4|clipr-appeal-center.com]]"
    ],
    clues: [
      { n: 1, title: "A fake support account", text: "A tick in the name is just a character anyone can type. A new account with 0 followers isn't the real team." },
      { n: 2, title: "Fear", text: "You're told you did something wrong, so you'll want to fix it fast." },
      { n: 3, title: "Rush", text: "\"24 hours\" leaves no time to check." },
      { n: 4, title: "Outside website", text: "Real appeals happen inside the app's own settings, not on another website." }
    ],
    hint: "Where would a real app warn you about your account?",
    takeaway: "Real warnings appear in the app's own notifications or settings, never as a DM with a link.",
    learn: "#baits"
  },

  // --- Safe ---------------------------------------------------------------------
  {
    id: "parcel-real",
    answer: "safe",
    channel: "sms",
    situation: "You ordered a phone case two days ago.",
    from: "SwiftPost",
    text: "SwiftPost: Your parcel [[1|SP4410 2938 MY]] is out for delivery today between 2pm and 6pm. [[2|Track it in the SwiftPost app.]] [[3|We will never ask you to pay by SMS.]]",
    clues: [
      { n: 1, title: "Matches what you did", text: "You did order something, and there's a tracking number you can check yourself." },
      { n: 2, title: "Sends you to the app", text: "No link to tap. It tells you to open the official app yourself." },
      { n: 3, title: "Asks for nothing", text: "No fee, no password, no rush." }
    ],
    hint: "Does it ask you to tap, pay or type anything?",
    takeaway: "Sender names can be faked, so judge what a message asks you to do. This one asks for nothing.",
    learn: "#compare"
  },
  {
    id: "bank-real",
    answer: "safe",
    channel: "email",
    situation: "You signed in to MyBank on your laptop a minute ago.",
    fromName: "MyBank",
    fromAddress: "[[1|alerts@mybank.com.my]]",
    subject: "New sign-in to your MyBank account",
    body: [
      "[[2|Hi Daniel]],",
      "Your account was signed in on Chrome (Windows) today at 8:14pm.",
      "[[3|If this was you, you don't need to do anything.]]",
      "If it wasn't you, [[4|open the MyBank app or call the number on the back of your card.]] We will never ask for your password or TAC."
    ],
    clues: [
      { n: 1, title: "The bank's own address", text: "It comes from mybank.com.my." },
      { n: 2, title: "Uses your name", text: "Your bank knows who you are." },
      { n: 3, title: "No rush, no action", text: "It matches what you just did, and asks you to do nothing." },
      { n: 4, title: "Points you to the app", text: "No login link. It tells you to use the official app or your card's number." }
    ],
    hint: "Does it match something you just did? Does it want anything from you?",
    takeaway: "Real alerts tell you what happened and let you act through the official app, never a login link.",
    learn: "#compare"
  },
  {
    id: "friend-real",
    answer: "safe",
    channel: "chat",
    situation: "You and Aina planned to study together this week.",
    app: "Messages",
    contact: "Aina 🌸",
    contactNote: "[[1|Saved contact · chatted yesterday]]",
    messages: [
      "Are we still meeting at the library at 3? 📚",
      "[[2|I'll bring the notes for the Biology quiz]]"
    ],
    clues: [
      { n: 1, title: "Someone you know", text: "Her saved number, in a chat you already have." },
      { n: 2, title: "Fits your plans, asks for nothing", text: "No link, no code, no money. Just your study plan." }
    ],
    hint: "Is anything being asked of you here?",
    takeaway: "Most messages are fine! A normal message fits your life and asks for nothing risky.",
    learn: "#compare"
  },
  {
    id: "game-event-real",
    answer: "safe",
    channel: "chat",
    situation: "This appears in the News tab inside the GameVault game.",
    app: "GameVault",
    contact: "GameVault",
    contactNote: "[[1|Official news · inside the game]]",
    messages: [
      "Weekend event is live! 🎮 [[2|Log in each day and open the Events tab to collect your rewards.]]",
      "[[3|No codes or passwords needed.]]"
    ],
    clues: [
      { n: 1, title: "Inside the real game", text: "It's in the game's own news, not a DM from a player." },
      { n: 2, title: "Rewards stay in the game", text: "You collect them in the Events tab, with no outside website." },
      { n: 3, title: "Asks for nothing", text: "No login on another site, no code, no password." }
    ],
    hint: "Where is this message, and where are the rewards collected?",
    takeaway: "Real game rewards are collected inside the game itself.",
    learn: "#baits"
  },
  {
    id: "school-real",
    answer: "safe",
    channel: "email",
    situation: "Your school uses StudyHub, and you really do have Assignment 3 this week.",
    fromName: "StudyHub",
    fromAddress: "[[1|no-reply@studyhub.edu.my]]",
    subject: "Reminder: Assignment 3 is due on Friday",
    body: [
      "Hi Daniel,",
      "This is a reminder that [[2|Assignment 3 for Computer Science]] is due on Friday at 11:59pm.",
      "[[3|Submit it through the StudyHub portal as usual.]] Ask your teacher if you have any questions."
    ],
    clues: [
      { n: 1, title: "The school's own address", text: "It comes from studyhub.edu.my, the school's real system." },
      { n: 2, title: "Matches your real work", text: "You really do have this assignment." },
      { n: 3, title: "Nothing unusual", text: "No link, no payment, no password. Just use the portal as you always do." }
    ],
    hint: "Does it fit what's really happening at school?",
    takeaway: "Real school messages match what you're doing and ask for nothing unusual.",
    learn: "#compare"
  },
  {
    id: "otp-requested",
    answer: "safe",
    channel: "sms",
    situation: "You tapped \"Log in\" on the ZoomCart app a few seconds ago.",
    from: "ZoomCart",
    text: "[[1|Your ZoomCart login code is 482913.]] It expires in 5 minutes. [[2|Never share this code with anyone, including ZoomCart staff.]]",
    clues: [
      { n: 1, title: "You asked for it", text: "You just tried to log in, so this code is expected." },
      { n: 2, title: "Warns you, asks for nothing", text: "It tells you not to share it, and wants nothing back." }
    ],
    hint: "Did you just do something that would send you a code?",
    takeaway: "A code you asked for is fine to type into the app yourself. If anyone then asks you for it, that's the scam.",
    learn: "#act"
  },
  {
    id: "order-real",
    answer: "safe",
    channel: "email",
    situation: "You just bought a phone case on ZoomCart.",
    fromName: "ZoomCart",
    fromAddress: "[[1|orders@zoomcart.com.my]]",
    subject: "Order confirmed: #ZC-58210",
    body: [
      "Hi Daniel, thanks for your order!",
      "[[2|Phone case (blue) × 1, RM19.90]]",
      "[[3|You can also check your order in the ZoomCart app.]]"
    ],
    button: "View order",
    linkTarget: "https://www.[[4|zoomcart.com.my]]/orders/ZC-58210",
    clues: [
      { n: 1, title: "The shop's own address", text: "It comes from zoomcart.com.my." },
      { n: 2, title: "Matches exactly what you bought", text: "Same item, same price." },
      { n: 3, title: "Offers the app instead", text: "You don't even need the link." },
      { n: 4, title: "A real link", text: "Links aren't bad by themselves. This one's owner is zoomcart.com.my, the shop." }
    ],
    hint: "It has a link. So who owns that link?",
    takeaway: "A link isn't always bad. Check who owns it and whether the message matches what you did.",
    learn: "#links"
  }
];
