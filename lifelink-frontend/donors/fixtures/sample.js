const
sampleConversations = [
    { user_id: 2, name: "Aarav Sharma", last_message: "Need A+ blood at City Hospital", unread: 2 },
    { user_id: 3, name: "Priya Mehta", last_message: "Donor is available by 4 PM", unread: 0 },
    { user_id: 4, name: "Rahul Verma", last_message: "Please share patient details", unread: 1 },
    { user_id: 5, name: "Sneha Iyer", last_message: "AB- urgently needed in Mumbai", unread: 3 },
    { user_id: 6, name: "Imran Khan", last_message: "I can donate tomorrow morning", unread: 0 },
    { user_id: 7, name: "Neha Patel", last_message: "Hospital location sent", unread: 0 },
    { user_id: 8, name: "Rohan Das", last_message: "Is O- still required?", unread: 1 },
    { user_id: 9, name: "Anjali Nair", last_message: "Thank you for arranging donors", unread: 0 },
    { user_id: 10, name: "Vikram Joshi", last_message: "Need 2 units of B+ blood", unread: 2 },
    { user_id: 11, name: "Fatima Sheikh", last_message: "I have contacted nearby donors", unread: 0 }
];

const sampleMessages = {
    2: [
        { content: "Hello, we urgently need A+ blood.", timestamp: "10:00 AM", is_sender: false },
        { content: "How many units are required?", timestamp: "10:02 AM", is_sender: true },
        { content: "Two units at City Hospital.", timestamp: "10:03 AM", is_sender: false },
        { content: "I will check with nearby donors.", timestamp: "10:05 AM", is_sender: true }
    ],

    3: [
        { content: "A donor is available by 4 PM.", timestamp: "09:15 AM", is_sender: false },
        { content: "That helps a lot, thank you.", timestamp: "09:17 AM", is_sender: true },
        { content: "Please confirm the blood group once.", timestamp: "09:18 AM", is_sender: false }
    ],

    4: [
        { content: "Please share patient details.", timestamp: "11:20 AM", is_sender: false },
        { content: "Patient is admitted in Ward 6.", timestamp: "11:22 AM", is_sender: true },
        { content: "Blood group is O+.", timestamp: "11:23 AM", is_sender: true },
        { content: "Understood, I will circulate the request.", timestamp: "11:25 AM", is_sender: false }
    ],

    5: [
        { content: "AB- urgently needed in Mumbai.", timestamp: "08:40 AM", is_sender: false },
        { content: "Which hospital?", timestamp: "08:42 AM", is_sender: true },
        { content: "Lilavati Hospital.", timestamp: "08:43 AM", is_sender: false },
        { content: "I know one rare donor, contacting now.", timestamp: "08:45 AM", is_sender: true }
    ],

    6: [
        { content: "I can donate tomorrow morning.", timestamp: "07:50 AM", is_sender: false },
        { content: "That would be great.", timestamp: "07:52 AM", is_sender: true },
        { content: "Please reach by 9 AM if possible.", timestamp: "07:53 AM", is_sender: true },
        { content: "Sure, I will be there.", timestamp: "07:55 AM", is_sender: false }
    ],

    7: [
        { content: "Hospital location sent.", timestamp: "01:10 PM", is_sender: false },
        { content: "Received, thank you.", timestamp: "01:11 PM", is_sender: true }
    ],

    8: [
        { content: "Is O- still required?", timestamp: "12:30 PM", is_sender: false },
        { content: "Yes, one donor still needed.", timestamp: "12:32 PM", is_sender: true },
        { content: "Okay, I can ask my friend.", timestamp: "12:34 PM", is_sender: false }
    ],

    9: [
        { content: "Thank you for arranging donors.", timestamp: "03:05 PM", is_sender: false },
        { content: "Glad the request was fulfilled.", timestamp: "03:06 PM", is_sender: true },
        { content: "The patient is stable now.", timestamp: "03:08 PM", is_sender: false }
    ],

    10: [
        { content: "Need 2 units of B+ blood.", timestamp: "06:40 AM", is_sender: false },
        { content: "Urgency level?", timestamp: "06:41 AM", is_sender: true },
        { content: "Needed before noon.", timestamp: "06:42 AM", is_sender: false },
        { content: "I will notify active donors nearby.", timestamp: "06:44 AM", is_sender: true }
    ],

    11: [
        { content: "I have contacted nearby donors.", timestamp: "05:20 PM", is_sender: false },
        { content: "Any responses yet?", timestamp: "05:22 PM", is_sender: true },
        { content: "Two people said they may come.", timestamp: "05:25 PM", is_sender: false }
    ]
};

sampleConversations.push(
    { user_id: 12, name: "Karan Singh", last_message: "Need donor for platelets", unread: 1 },
    { user_id: 13, name: "Meera Rao", last_message: "Request fulfilled successfully", unread: 0 },
    { user_id: 14, name: "Dev Malhotra", last_message: "Can reach hospital in 30 minutes", unread: 2 }
);

sampleMessages[12] = [
    { content: "Need donor for platelets.", timestamp: "02:00 PM", is_sender: false },
    { content: "I will check availability.", timestamp: "02:02 PM", is_sender: true }
];

sampleMessages[13] = [
    { content: "Request fulfilled successfully.", timestamp: "04:10 PM", is_sender: false },
    { content: "Great news, thanks for updating.", timestamp: "04:11 PM", is_sender: true }
];

sampleMessages[14] = [
    { content: "Can reach hospital in 30 minutes.", timestamp: "09:00 AM", is_sender: false },
    { content: "Please proceed, patient side has been informed.", timestamp: "09:02 AM", is_sender: true }
];