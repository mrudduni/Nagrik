import type { LanguageCode } from "@/types"

export interface TranslationDictionary {
  nav: {
    ai_assistant: string
    services: string
    applications: string
    issues: string
    profile: string
    switch_to_gov: string
    switching_to_gov: string
    switch_to_citizen: string
  }
  topbar: {
    search_placeholder: string
    search_command_title: string
    call_nagrik: string
    notifications: string
    my_profile: string
    preferences: string
    sign_out: string
    choose_language: string
  }
  chat: {
    greeting: string
    subtitle: string
    welcome_message: string
    placeholder: string
    disclaimer: string
    listen: string
    pause: string
    resume: string
    stop: string
    speaking: string
    paused: string
    attach_image: string
    attach_doc: string
    voice_input: string
    voice_recording: string
    voice_processing: string
    sources: string
    view_details: string
    compare: string
    apply: string
    check_status: string
  }
  widgets: {
    recommended_schemes: string
    active_applications: string
    reported_issues: string
    view_all: string
    no_applications: string
    no_issues: string
  }
  services: {
    explore_title: string
    explore_subtitle: string
    search_placeholder: string
    all_categories: string
    apply_now: string
    check_eligibility: string
    view_details: string
    compare_schemes: string
  }
}

export const TRANSLATIONS: Record<LanguageCode, TranslationDictionary> = {
  en: {
    nav: {
      ai_assistant: "AI Assistant",
      services: "Government Services",
      applications: "My Applications",
      issues: "Civic Issues",
      profile: "Profile & Vault",
      switch_to_gov: "Switch to Government Portal",
      switching_to_gov: "Switching to Gov...",
      switch_to_citizen: "Switch to Citizen Portal",
    },
    topbar: {
      search_placeholder: "Search NAGRIK...",
      search_command_title: "Type a command or search...",
      call_nagrik: "Call NAGRIK Helpline",
      notifications: "Notifications",
      my_profile: "My Profile",
      preferences: "Preferences",
      sign_out: "Sign out",
      choose_language: "Choose language",
    },
    chat: {
      greeting: "Namaste",
      subtitle: "Ask anything about schemes, applications, or civic issues.",
      welcome_message:
        "Namaste! I'm your NAGRIK AI assistant. I can help you discover government schemes, check eligibility, fill out applications, track their status, or report a civic issue — in text or voice. What would you like help with today?",
      placeholder: "Ask about schemes, applications, or report an issue...",
      disclaimer: "NAGRIK AI can make mistakes. Always verify critical information from official sources.",
      listen: "Listen",
      pause: "Pause",
      resume: "Resume",
      stop: "Stop",
      speaking: "Speaking...",
      paused: "Paused",
      attach_image: "Attach image",
      attach_doc: "Attach document",
      voice_input: "Voice input",
      voice_recording: "Listening...",
      voice_processing: "Processing your voice message...",
      sources: "Sources",
      view_details: "View Scheme Details",
      compare: "Compare Schemes",
      apply: "Apply for Scheme",
      check_status: "View Grievance Status",
    },
    widgets: {
      recommended_schemes: "Recommended For You",
      active_applications: "Active Applications",
      reported_issues: "Reported Civic Issues",
      view_all: "View all",
      no_applications: "No active applications",
      no_issues: "No open civic issues",
    },
    services: {
      explore_title: "Government Services",
      explore_subtitle: "Browse and apply for central and state welfare schemes",
      search_placeholder: "Search schemes by name, keyword, or benefits...",
      all_categories: "All Categories",
      apply_now: "Apply Now",
      check_eligibility: "Check Eligibility",
      view_details: "View Details",
      compare_schemes: "Compare Schemes",
    },
  },

  hi: {
    nav: {
      ai_assistant: "एआई सहायक",
      services: "सरकारी सेवाएं",
      applications: "मेरे आवेदन",
      issues: "नागरिक समस्याएं",
      profile: "प्रोफ़ाइल और वॉल्ट",
      switch_to_gov: "सरकारी पोर्टल पर जाएं",
      switching_to_gov: "सरकारी पोर्टल लोड हो रहा है...",
      switch_to_citizen: "नागरिक पोर्टल पर जाएं",
    },
    topbar: {
      search_placeholder: "नागरिक में खोजें...",
      search_command_title: "खोजें या कमांड टाइप करें...",
      call_nagrik: "नागरिक हेल्पलाइन पर कॉल करें",
      notifications: "सूचनाएं",
      my_profile: "मेरी प्रोफ़ाइल",
      preferences: "प्राथमिकताएं",
      sign_out: "लॉग आउट",
      choose_language: "भाषा चुनें",
    },
    chat: {
      greeting: "नमस्ते",
      subtitle: "सरकारी योजनाओं, आवेदनों या नागरिक समस्याओं के बारे में कुछ भी पूछें।",
      welcome_message:
        "नमस्ते! मैं आपका नागरिक एआई सहायक हूँ। मैं आपको सरकारी योजनाओं को खोजने, पात्रता जाँचने, आवेदन पत्र भरने, स्थिति ट्रैक करने या नागरिक समस्या दर्ज करने में मदद कर सकता हूँ — टेक्स्ट या आवाज़ में। आज मैं आपकी क्या मदद कर सकता हूँ?",
      placeholder: "योजनाओं, आवेदनों के बारे में पूछें या समस्या दर्ज करें...",
      disclaimer: "नागरिक एआई से त्रुटियां हो सकती हैं। हमेशा आधिकारिक स्रोतों से पुष्टि करें।",
      listen: "सुनें",
      pause: "रोकें",
      resume: "जारी रखें",
      stop: "बंद करें",
      speaking: "बोल रहा है...",
      paused: "रुका हुआ",
      attach_image: "चित्र जोड़ें",
      attach_doc: "दस्तावेज़ जोड़ें",
      voice_input: "ध्वनि इनपुट",
      voice_recording: "सुन रहा हूँ...",
      voice_processing: "आपकी आवाज़ का विश्लेषण किया जा रहा है...",
      sources: "स्रोत्र",
      view_details: "योजना विवरण देखें",
      compare: "योजनाओं की तुलना करें",
      apply: "योजना के लिए आवेदन करें",
      check_status: "शिकायत की स्थिति देखें",
    },
    widgets: {
      recommended_schemes: "आपके लिए अनुशंसित",
      active_applications: "सक्रिय आवेदन",
      reported_issues: "दर्ज की गई समस्याएं",
      view_all: "सभी देखें",
      no_applications: "कोई सक्रिय आवेदन नहीं है",
      no_issues: "कोई खुली समस्या नहीं है",
    },
    services: {
      explore_title: "सरकारी सेवाएं",
      explore_subtitle: "केंद्र और राज्य सरकार की कल्याणकारी योजनाएं खोजें और आवेदन करें",
      search_placeholder: "योजना नाम, कीवर्ड या लाभ द्वारा खोजें...",
      all_categories: "सभी श्रेणियां",
      apply_now: "अभी आवेदन करें",
      check_eligibility: "पात्रता जांचें",
      view_details: "विवरण देखें",
      compare_schemes: "योजनाओं की तुलना करें",
    },
  },

  bn: {
    nav: {
      ai_assistant: "এআই সহকারী",
      services: "সরকারি সেবা",
      applications: "আমার আবেদন",
      issues: "নাগরিক সমস্যা",
      profile: "প্রোফাইল এবং ভল্ট",
      switch_to_gov: "সরকারি পোর্টালে যান",
      switching_to_gov: "সরকারি পোর্টাল লোড হচ্ছে...",
      switch_to_citizen: "নাগরিক পোর্টালে যান",
    },
    topbar: {
      search_placeholder: "নাগরিকে অনুসন্ধান করুন...",
      search_command_title: "অনুসন্ধান করুন...",
      call_nagrik: "নাগরিক হেল্পলাইনে কল করুন",
      notifications: "বিজ্ঞপ্তি",
      my_profile: "আমার প্রোফাইল",
      preferences: "পছন্দসমূহ",
      sign_out: "লগ আউট",
      choose_language: "ভাষা নির্বাচন করুন",
    },
    chat: {
      greeting: "নমস্কার",
      subtitle: "যোজনা, আবেদন বা নাগরিক সমস্যা সম্পর্কে যে কোনও কিছু জিজ্ঞাসা করুন।",
      welcome_message:
        "নমস্কার! আমি আপনার নাগরিক এআই সহকারী। সরকারি প্রকল্প খোঁজা, যোগ্যতা যাচাই, আবেদন করা এবং সমস্যা জানাতে আমি সাহায্য করতে পারি। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
      placeholder: "যোজনা বা আবেদন সম্পর্কে জিজ্ঞাসা করুন...",
      disclaimer: "নাগরিক এআই ভুল করতে পারে। সর্বদা অফিসিয়াল তথ্য যাচাই করুন।",
      listen: "শুনুন",
      pause: "থামান",
      resume: "চালিয়ে যান",
      stop: "বন্ধ করুন",
      speaking: "কথা বলছে...",
      paused: "স্থগিত",
      attach_image: "ছবি সংযুক্ত করুন",
      attach_doc: "ডকুমেন্ট সংযুক্ত করুন",
      voice_input: "ভয়েস ইনপুট",
      voice_recording: "শুনছি...",
      voice_processing: "ভয়েস প্রসেস হচ্ছে...",
      sources: "উৎস",
      view_details: "বিবরণ দেখুন",
      compare: "তুলনা করুন",
      apply: "আবেদন করুন",
      check_status: "স্ট্যাটাস দেখুন",
    },
    widgets: {
      recommended_schemes: "আপনার জন্য প্রস্তাবিত",
      active_applications: "সক্রিয় আবেদন",
      reported_issues: "নাগরিক সমস্যা",
      view_all: "সব দেখুন",
      no_applications: "কোনো সক্রিয় আবেদন নেই",
      no_issues: "কোনো সমস্যা নেই",
    },
    services: {
      explore_title: "সরকারি সেবা",
      explore_subtitle: "কেন্দ্র ও রাজ্য সরকারের জনকল্যাণমূলক প্রকল্পসমূহ",
      search_placeholder: "প্রকল্পের নাম দিয়ে খুঁজুন...",
      all_categories: "সকল বিভাগ",
      apply_now: "আবেদন করুন",
      check_eligibility: "যোগ্যতা যাচাই করুন",
      view_details: "বিস্তারিত দেখুন",
      compare_schemes: "প্রকল্প তুলনা করুন",
    },
  },

  ta: {
    nav: {
      ai_assistant: "AI உதவியாளர்",
      services: "அரசு சேவைகள்",
      applications: "என் விண்ணப்பங்கள்",
      issues: "குடிமைப் பிரச்சனைகள்",
      profile: "சுயவிவரம் & வால்ட்",
      switch_to_gov: "அரசு போர்ட்டலுக்கு மாறவும்",
      switching_to_gov: "அரசு போர்டல் மாறுகிறது...",
      switch_to_citizen: "குடிமக்கள் போர்ட்டலுக்கு மாறவும்",
    },
    topbar: {
      search_placeholder: "NAGRIK-ல் தேடவும்...",
      search_command_title: "தேடவும் அல்லது கட்டளையிடவும்...",
      call_nagrik: "NAGRIK உதவி எண்",
      notifications: "அறிவிப்புகள்",
      my_profile: "என் சுயவிவரம்",
      preferences: "விருப்பத்தேர்வுகள்",
      sign_out: "வெளியேறு",
      choose_language: "மொழியைத் தேர்ந்தெடுக்கவும்",
    },
    chat: {
      greeting: "வணக்கம்",
      subtitle: "திட்டங்கள், விண்ணப்பங்கள் அல்லது குடிமைப் பிரச்சனைகள் பற்றி எதையும் கேளுங்கள்.",
      welcome_message:
        "வணக்கம்! நான் உங்கள் NAGRIK AI உதவியாளர். அரசு திட்டங்களை கண்டறிய, தகுதியை சரிபார்க்க, விண்ணப்பங்களை சமர்ப்பிக்க நான் உங்களுக்கு உதவ முடியும். இன்று உங்களுக்கு எவ்வாறு உதவ வேண்டும்?",
      placeholder: "திட்டங்கள், விண்ணப்பங்கள் அல்லது பிரச்சனைகள் பற்றி கேட்கவும்...",
      disclaimer: "NAGRIK AI தவறுகளைச் செய்யக்கூடும். அதிகாரப்பூர்வ தகவல்களை சரிபார்க்கவும்.",
      listen: "கேளுங்கள்",
      pause: "நிறுத்து",
      resume: "தொடரவும்",
      stop: "முடி",
      speaking: "பேசுகிறது...",
      paused: "நிறுத்தப்பட்டது",
      attach_image: "படம் இணைக்கவும்",
      attach_doc: "ஆவணம் இணைக்கவும்",
      voice_input: "குரல் பதிவு",
      voice_recording: "கேட்கிறது...",
      voice_processing: "குரல் செயலாக்கப்படுகிறது...",
      sources: "ஆதாரங்கள்",
      view_details: "திட்ட விவரங்களைக் காண்க",
      compare: "திட்டங்களை ஒப்பிடவும்",
      apply: "திட்டத்திற்கு விண்ணப்பிக்கவும்",
      check_status: "நிலை அறிய",
    },
    widgets: {
      recommended_schemes: "உங்களுக்காக பரிந்துரைக்கப்படுகிறது",
      active_applications: "செயலில் உள்ள விண்ணப்பங்கள்",
      reported_issues: "பதிவு செய்யப்பட்ட பிரச்சனைகள்",
      view_all: "அனைத்தையும் காண்க",
      no_applications: "விண்ணப்பங்கள் எதுவும் இல்லை",
      no_issues: "பிரச்சனைகள் எதுவும் இல்லை",
    },
    services: {
      explore_title: "அரசு சேவைகள்",
      explore_subtitle: "மத்திய மற்றும் மாநில நலத்திட்டங்களை கண்டறிந்து விண்ணப்பிக்கவும்",
      search_placeholder: "திட்டங்களின் பெயரால் தேடவும்...",
      all_categories: "அனைத்து பிரிவுகளும்",
      apply_now: "இப்போது விண்ணப்பிக்கவும்",
      check_eligibility: "தகுதியை சரிபார்க்கவும்",
      view_details: "விவரங்களைக் காண்க",
      compare_schemes: "திட்டங்களை ஒப்பிடவும்",
    },
  },

  te: {
    nav: {
      ai_assistant: "AI సహాయకుడు",
      services: "ప్రభుత్వ సేవలు",
      applications: "నా దరఖాస్తులు",
      issues: "పౌర సమస్యలు",
      profile: "ప్రొఫైల్ & వాల్ట్",
      switch_to_gov: "ప్రభుత్వ పోర్టల్‌కు మారండి",
      switching_to_gov: "ప్రభుత్వ పోర్టల్ మారుతోంది...",
      switch_to_citizen: "పౌరుల పోర్టల్‌కు మారండి",
    },
    topbar: {
      search_placeholder: "NAGRIK లో శోధించండి...",
      search_command_title: "శోధించండి...",
      call_nagrik: "NAGRIK హెల్ప్‌లైన్",
      notifications: "నోటిఫికేషన్లు",
      my_profile: "నా ప్రొఫైల్",
      preferences: "ప్రాధాన్యతలు",
      sign_out: "లాగౌట్",
      choose_language: "భాషను ఎంచుకోండి",
    },
    chat: {
      greeting: "నమస్కారం",
      subtitle: "పథకాలు, దరఖాస్తులు లేదా పౌర సమస్యల గురించి ఏదైనా అడగండి.",
      welcome_message:
        "నమస్కారం! నేను మీ NAGRIK AI సహాయకుడిని. ప్రభుత్వ పథకాలను కనుగొనడం, అర్హత తనిఖీ మరియు దరఖాస్తు చేయడంలో మీకు సహాయపడతాను. ఈరోజు మీకు ఎలా సహాయపడాలి?",
      placeholder: "పథకాలు, దరఖాస్తుల గురించి అడగండి...",
      disclaimer: "NAGRIK AI తప్పులు చేయవచ్చు. అధికారిక సమాచారాన్ని ధృవీకరించండి.",
      listen: "వినండి",
      pause: "ఆపండి",
      resume: "కొనసాగించండి",
      stop: "ఆపు",
      speaking: "మాట్లాడుతోంది...",
      paused: "ఆగింది",
      attach_image: "చిత్రాన్ని జోడించండి",
      attach_doc: "పత్రాన్ని జోడించండి",
      voice_input: "వాయిస్ ఇన్‌పుట్",
      voice_recording: "వింటోంది...",
      voice_processing: "ప్రాసెస్ చేస్తోంది...",
      sources: "మూలాలు",
      view_details: "వివరాలు చూడండి",
      compare: "పోల్చండి",
      apply: "దరఖాస్తు చేసుకోండి",
      check_status: "స్థితిని తనిఖీ చేయండి",
    },
    widgets: {
      recommended_schemes: "మీ కోసం సిఫార్సు చేయబడింది",
      active_applications: "క్రియాశీల దరఖాస్తులు",
      reported_issues: "నమోదైన సమస్యలు",
      view_all: "అన్నీ చూడండి",
      no_applications: "దరఖాస్తులు లేవు",
      no_issues: "సమస్యలు లేవు",
    },
    services: {
      explore_title: "ప్రభుత్వ సేవలు",
      explore_subtitle: "కేంద్ర మరియు రాష్ట్ర సంక్షేమ పథకాలను అన్వేషించండి",
      search_placeholder: "పథకాల పేరుతో శోధించండి...",
      all_categories: "అన్ని వర్గాలు",
      apply_now: "ఇప్పుడే దరఖాస్తు చేసుకోండి",
      check_eligibility: "అర్హతను తనిఖీ చేయండి",
      view_details: "వివరాలు చూడండి",
      compare_schemes: "పథకాలను పోల్చండి",
    },
  },

  mr: {
    nav: {
      ai_assistant: "एआय सहाय्यक",
      services: "शासकीय सेवा",
      applications: "माझे अर्ज",
      issues: "नागरी समस्या",
      profile: "प्रोफाइल आणि व्हॉल्ट",
      switch_to_gov: "शासकीय पोर्टलवर जा",
      switching_to_gov: "शासकीय पोर्टल लोड होत आहे...",
      switch_to_citizen: "नागरिक पोर्टलवर जा",
    },
    topbar: {
      search_placeholder: "नागरिक मध्ये शोधा...",
      search_command_title: "कमांड टाइप करा किंवा शोधा...",
      call_nagrik: "नागरिक हेल्पलाइनवर कॉल करा",
      notifications: "सूचना",
      my_profile: "माझी प्रोफाइल",
      preferences: "प्राधान्ये",
      sign_out: "साइन आउट",
      choose_language: "भाषा निवडा",
    },
    chat: {
      greeting: "नमस्कार",
      subtitle: "योजना, अर्ज किंवा नागरी समस्यांबद्दल काहीही विचारा.",
      welcome_message:
        "नमस्कार! मी तुमचा नागरिक एआय सहाय्यक आहे. मी तुम्हाला सरकारी योजना शोधण्यात, पात्रता तपासण्यात, अर्ज भरण्यात किंवा समस्या नोंदवण्यात मदत करू शकतो. आज मी तुम्हाला कशी मदत करू?",
      placeholder: "योजना किंवा अर्जांबद्दल विचारा...",
      disclaimer: "नागरिक एआय कडून त्रुटी होऊ शकतात. नेहमी अधिकृत माहिती तपासा.",
      listen: "ऐका",
      pause: "थांबवा",
      resume: "पुढे सुरू ठेवा",
      stop: "बंद करा",
      speaking: "बोलत आहे...",
      paused: "थांबवले",
      attach_image: "चित्र जोडा",
      attach_doc: "कागदपत्र जोडा",
      voice_input: "आवाज इनपुट",
      voice_recording: "ऐकत आहे...",
      voice_processing: "आवाजावर प्रक्रिया सुरू आहे...",
      sources: "स्रोत",
      view_details: "तपशील पहा",
      compare: "योजनांची तुलना करा",
      apply: "अर्ज करा",
      check_status: "तक्रार स्थिती पहा",
    },
    widgets: {
      recommended_schemes: "तुमच्यासाठी शिफारस केलेले",
      active_applications: "सक्रिय अर्ज",
      reported_issues: "नोंदवलेल्या समस्या",
      view_all: "सर्व पहा",
      no_applications: "सक्रिय अर्ज नाहीत",
      no_issues: "समस्या नाहीत",
    },
    services: {
      explore_title: "शासकीय सेवा",
      explore_subtitle: "केंद्र आणि राज्य सरकारच्या कल्याणकारी योजना शोधा आणि अर्ज करा",
      search_placeholder: "योजना शोधा...",
      all_categories: "सर्व वर्ग",
      apply_now: "आता अर्ज करा",
      check_eligibility: "पात्रता तपासा",
      view_details: "तपशील पहा",
      compare_schemes: "योजनांची तुलना करा",
    },
  },

  gu: {
    nav: {
      ai_assistant: "AI સહાયક",
      services: "સરકારી સેવાઓ",
      applications: "મારી અરજીઓ",
      issues: "નાગરિક સમસ્યાઓ",
      profile: "પ્રોફાઇલ અને વૉલ્ટ",
      switch_to_gov: "સરકારી પોર્ટલ પર જાઓ",
      switching_to_gov: "સરકારી પોર્ટલ લોડ થઈ રહ્યું છે...",
      switch_to_citizen: "નાગરિક પોર્ટલ પર જાઓ",
    },
    topbar: {
      search_placeholder: "NAGRIK માં શોધો...",
      search_command_title: "શોધો...",
      call_nagrik: "NAGRIK હેલ્પલાઇન",
      notifications: "સૂચનાઓ",
      my_profile: "મારી પ્રોફાઇલ",
      preferences: "પસંદગીઓ",
      sign_out: "સાઇન આઉટ",
      choose_language: "ભાષા પસંદ કરો",
    },
    chat: {
      greeting: "નમસ્તે",
      subtitle: "યોજનાઓ, અરજીઓ અથવા નાગરિક સમસ્યાઓ વિશે કંઈપણ પૂછો.",
      welcome_message:
        "નમસ્તે! હું તમારો નાગરિક AI સહાયક છું. સરકારી યોજનાઓ શોધવા, પાત્રતા ચકાસવા, અરજી કરવા અને સમસ્યા નોંધવામાં મદદ કરી શકું છું. આજે હું તમને કેવી રીતે મદદ કરી શકું?",
      placeholder: "યોજનાઓ અથવા અરજીઓ વિશે પૂછો...",
      disclaimer: "NAGRIK AI ભૂલો કરી શકે છે. સત્તાવાર સ્ત્રોતોમાંથી ચકાસો.",
      listen: "સાંભળો",
      pause: "અટકાવો",
      resume: "ચાલુ રાખો",
      stop: "બંધ કરો",
      speaking: "બોલી રહ્યું છે...",
      paused: "અટકેલ",
      attach_image: "ચિત્ર જોડો",
      attach_doc: "દસ્તાવેજ જોડો",
      voice_input: "વૉઇસ ઇનપુટ",
      voice_recording: "સાંભળી રહ્યું છે...",
      voice_processing: "પ્રક્રિયા ચાલુ છે...",
      sources: "સ્ત્રોતો",
      view_details: "વિગતો જુઓ",
      compare: "સરખામણી કરો",
      apply: "અરજી કરો",
      check_status: "સ્થિતિ જુઓ",
    },
    widgets: {
      recommended_schemes: "તમારા માટે ભલામણ કરેલ",
      active_applications: "સક્રિય અરજીઓ",
      reported_issues: "નોંધાયેલી સમસ્યાઓ",
      view_all: "બધું જુઓ",
      no_applications: "કોઈ સક્રિય અરજી નથી",
      no_issues: "કોઈ સમસ્યા નથી",
    },
    services: {
      explore_title: "સરકારી સેવાઓ",
      explore_subtitle: "કેન્દ્ર અને રાજ્ય સરકારની કલ્યાણકારી યોજનાઓ",
      search_placeholder: "યોજનાઓ શોધો...",
      all_categories: "બધી શ્રેણીઓ",
      apply_now: "હમણાં અરજી કરો",
      check_eligibility: "પાત્રતા તપાસો",
      view_details: "વિગતો જુઓ",
      compare_schemes: "યોજનાઓની સરખામણી કરો",
    },
  },

  kn: {
    nav: {
      ai_assistant: "AI ಸಹಾಯಕ",
      services: "ಸರ್ಕಾರಿ ಸೇವೆಗಳು",
      applications: "ನನ್ನ ಅರ್ಜಿಗಳು",
      issues: "ನಾಗರಿಕ ಸಮಸ್ಯೆಗಳು",
      profile: "ಪ್ರೊಫೈಲ್ ಮತ್ತು ವಾಲ್ಟ್",
      switch_to_gov: "ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್‌ಗೆ ಬದಲಿಸಿ",
      switching_to_gov: "ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
      switch_to_citizen: "ನಾಗರಿಕ ಪೋರ್ಟಲ್‌ಗೆ ಬದಲಿಸಿ",
    },
    topbar: {
      search_placeholder: "NAGRIK ನಲ್ಲಿ ಹುಡುಕಿ...",
      search_command_title: "ಹುಡುಕಿ...",
      call_nagrik: "NAGRIK ಸಹಾಯವಾಣಿ",
      notifications: "ಅಧಿಸೂಚನೆಗಳು",
      my_profile: "ನನ್ನ ಪ್ರೊಫೈಲ್",
      preferences: "ಆದ್ಯತೆಗಳು",
      sign_out: "ಸೈನ್ ಔಟ್",
      choose_language: "ಭಾಷೆಯನ್ನು ಆರಿಸಿ",
    },
    chat: {
      greeting: "ನಮಸ್ಕಾರ",
      subtitle: "ಯೋಜನೆಗಳು, ಅರ್ಜಿಗಳು ಅಥವಾ ನಾಗರಿಕ ಸಮಸ್ಯೆಗಳ ಬಗ್ಗೆ ಏನನ್ನಾದರೂ ಕೇಳಿ.",
      welcome_message:
        "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ NAGRIK AI ಸಹಾಯಕ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು, ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಲು, ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಮತ್ತು ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಲು ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
      placeholder: "ಯೋಜನೆಗಳು ಅಥವಾ ಅರ್ಜಿಗಳ ಬಗ್ಗೆ ಕೇಳಿ...",
      disclaimer: "NAGRIK AI ತಪ್ಪುಗಳನ್ನು ಮಾಡಬಹುದು. ಅಧಿಕೃತ ಮೂಲಗಳಿಂದ ದೃಢೀಕರಿಸಿ.",
      listen: "ಕೇಳಿ",
      pause: "ವಿರಾಮ",
      resume: "ಮುಂದುವರಿಸಿ",
      stop: "ನಿಲ್ಲಿಸಿ",
      speaking: "ಮಾತನಾಡುತ್ತಿದೆ...",
      paused: "ವಿರಾಮದಲ್ಲಿದೆ",
      attach_image: "ಚಿತ್ರ ಲಗತ್ತಿಸಿ",
      attach_doc: "ದಾಖಲೆ ಲಗತ್ತಿಸಿ",
      voice_input: "ಧ್ವನಿ ಇನ್‌ಪುಟ್",
      voice_recording: "ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದೆ...",
      voice_processing: "ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ...",
      sources: "ಮೂಲಗಳು",
      view_details: "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
      compare: "ಹೋಲಿಕೆ ಮಾಡಿ",
      apply: "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
      check_status: "ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ",
    },
    widgets: {
      recommended_schemes: "ನಿಮಗಾಗಿ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ",
      active_applications: "ಸಕ್ರಿಯ ಅರ್ಜಿಗಳು",
      reported_issues: "ವರದಿ ಮಾಡಿದ ಸಮಸ್ಯೆಗಳು",
      view_all: "ಎಲ್ಲವನ್ನೂ ವೀಕ್ಷಿಸಿ",
      no_applications: "ಯಾವುದೇ ಅರ್ಜಿಗಳಿಲ್ಲ",
      no_issues: "ಯಾವುದೇ ಸಮಸ್ಯೆಗಳಿಲ್ಲ",
    },
    services: {
      explore_title: "ಸರ್ಕಾರಿ ಸೇವೆಗಳು",
      explore_subtitle: "ಕೇಂದ್ರ ಮತ್ತು ರಾಜ್ಯ ಸರ್ಕಾರದ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು",
      search_placeholder: "ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ...",
      all_categories: "ಎಲ್ಲಾ ವರ್ಗಗಳು",
      apply_now: "ಈಗಲೇ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
      check_eligibility: "ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ",
      view_details: "ವಿವರಗಳನ್ನು ನೋಡಿ",
      compare_schemes: "ಯೋಜನೆಗಳನ್ನು ಹೋಲಿಸಿ",
    },
  },
}

export function getTranslation(lang: LanguageCode): TranslationDictionary {
  return TRANSLATIONS[lang] || TRANSLATIONS.en
}
