package ai.vivian.companion

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.net.Uri
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.provider.ContactsContract
import android.provider.Settings
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.*
import java.util.Locale

class MainActivity : Activity(), TextToSpeech.OnInitListener {
    private val forest = Color.rgb(25, 66, 50)
    private val mint = Color.rgb(221, 241, 226)
    private val pageBackgroundColor = Color.rgb(249, 249, 245)
    private lateinit var content: LinearLayout
    private var tts: TextToSpeech? = null
    private val speechRequest = 101
    private val contactRequest = 102
    private var lastTab = "Home"
    private var input: EditText? = null
    private var result: TextView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tts = TextToSpeech(this, this)
        showTab("Home")
    }
    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) tts?.language = Locale.getDefault()
    }
    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }
    private fun label(text: String, size: Float = 16f, bold: Boolean = false): TextView =
        TextView(this).apply {
            this.text = text
            textSize = size
            setTextColor(forest)
            if (bold) setTypeface(null, Typeface.BOLD)
            setPadding(0, dp(8), 0, dp(8))
        }
    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
    private fun panel(title: String, subtitle: String, action: (() -> Unit)? = null) {
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(14), dp(18), dp(14))
            setBackgroundColor(mint)
        }
        card.addView(label(title, 17f, true))
        card.addView(label(subtitle, 13f))
        if (action != null) {
            card.isClickable = true
            card.setOnClickListener { action() }
        }
        content.addView(card, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) })
    }
    private fun button(text: String, action: () -> Unit) {
        val b = Button(this).apply {
            this.text = text
            setTextColor(forest)
            setOnClickListener { action() }
        }
        content.addView(b, LinearLayout.LayoutParams(-1, -2))
    }
    private fun safeStart(intent: Intent) {
        try { startActivity(intent) }
        catch (_: ActivityNotFoundException) { toast("No compatible app found") }
        catch (_: SecurityException) { toast("Action not permitted by Android") }
    }
    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_LONG).show()
    private fun openApp(name: String, pkg: String) {
        val launch = packageManager.getLaunchIntentForPackage(pkg)
        if (launch != null) safeStart(launch) else toast("$name is unavailable")
    }
    private fun showTab(tab: String) {
        lastTab = tab
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(pageBackgroundColor) }
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(12))
            setBackgroundColor(forest)
        }
        header.addView(TextView(this).apply {
            text = "VIVIAN  /  $tab"
            textSize = 22f
            setTextColor(Color.WHITE)
            setTypeface(null, Typeface.BOLD)
        })
        header.addView(TextView(this).apply {
            text = "Your personal Android assistant"
            textSize = 12f
            setTextColor(Color.rgb(210, 236, 217))
        })
        root.addView(header)
        val scroll = ScrollView(this).apply { isFillViewport = true }
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(18), dp(18), dp(18))
        }
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        val nav = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(4), dp(5), dp(4), dp(5))
            setBackgroundColor(mint)
        }
        listOf("Home", "Assistant", "Phone", "Apps", "Settings").forEach { item ->
            nav.addView(Button(this).apply {
                text = item
                textSize = 10f
                isAllCaps = false
                setOnClickListener { showTab(item) }
            }, LinearLayout.LayoutParams(0, dp(52), 1f))
        }
        root.addView(nav)
        setContentView(root)
        when (tab) {
            "Home" -> home()
            "Assistant" -> assistant()
            "Phone" -> phone()
            "Apps" -> apps()
            else -> settings()
        }
    }
    private fun home() {
        content.addView(label("Good to see you.", 25f, true))
        val battery = getSystemService(BATTERY_SERVICE) as BatteryManager
        val level = battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        panel("Device connected locally", "${Build.MANUFACTURER} ${Build.MODEL} · Android ${Build.VERSION.RELEASE} · Battery $level%")
        panel("Vivian Assistant", "Speak or type a command to open an app, dial a number, or prepare an SMS.") { showTab("Assistant") }
        panel("Phone & communication", "Dialer, SMS composer and contact picker. You approve the final action.") { showTab("Phone") }
        panel("Privacy", "No cloud pairing or notification reading enabled. All current commands run on this phone.") { showTab("Settings") }
    }
    private fun assistant() {
        content.addView(label("What can I do for you?", 23f, true))
        content.addView(label("Try: open WhatsApp, call 1234567890, text 1234567890, open Gmail.", 13f))
        input = EditText(this).apply {
            hint = "Type a command..."
            setSingleLine(false)
            minLines = 2
        }
        content.addView(input)
        button("Run command") { execute(input?.text?.toString().orEmpty()) }
        button("Speak a command") {
            val i = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Vivian")
            }
            try { startActivityForResult(i, speechRequest) }
            catch (_: ActivityNotFoundException) { toast("Speech recognition is not available on this device") }
        }
        result = label("Vivian is ready. Commands are processed locally in v0.2.", 14f)
        content.addView(result)
        panel("Coming later", "AI chat, ChatGPT/Claude knowledge, remote pairing, and advanced automation require additional integration.")
    }
    private fun execute(raw: String) {
        val command = raw.trim().lowercase(Locale.ROOT)
        val apps = mapOf(
            "whatsapp" to "com.whatsapp",
            "gmail" to "com.google.android.gm",
            "youtube" to "com.google.android.youtube",
            "chrome" to "com.android.chrome",
            "spotify" to "com.spotify.music"
        )
        val match = apps.entries.firstOrNull { command.contains(it.key) }
        val response = when {
            command.isBlank() -> "Enter a command first."
            command.startsWith("open ") && match != null -> {
                openApp(match.key, match.value); "Opening ${match.key}."
            }
            command.startsWith("call ") || command.startsWith("dial ") -> {
                val number = raw.substringAfter(' ').trim()
                if (number.matches(Regex("[+0-9 ()-]{3,25}"))) {
                    safeStart(Intent(Intent.ACTION_DIAL, Uri.parse("tel:${Uri.encode(number)}")))
                    "Opening dialer. Confirm the call on your phone."
                } else "For now, enter a phone number after 'call'."
            }
            command.startsWith("text ") || command.startsWith("sms ") -> {
                val number = raw.substringAfter(' ').trim()
                if (number.matches(Regex("[+0-9 ()-]{3,25}"))) {
                    safeStart(Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:${Uri.encode(number)}")))
                    "Opening SMS composer. Review before sending."
                } else "For now, enter a phone number after 'text'."
            }
            command == "settings" -> { showTab("Settings"); "Opening settings." }
            else -> "I can currently open supported apps, dial numbers, and prepare SMS messages. AI chat is not connected yet."
        }
        result?.text = response
        tts?.speak(response, TextToSpeech.QUEUE_FLUSH, null, "vivian-response")
    }
    private fun phone() {
        content.addView(label("Phone & telecom", 23f, true))
        panel("Calls", "Use the system dialer. Vivian cannot place calls silently.")
        button("Open dialer") { safeStart(Intent(Intent.ACTION_DIAL)) }
        button("Choose a contact") {
            safeStartForResult(Intent(Intent.ACTION_PICK, ContactsContract.Contacts.CONTENT_URI), contactRequest)
        }
        panel("Messages", "Compose an SMS in your messaging app; you decide whether to send.")
        button("Compose SMS") { safeStart(Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:"))) }
        panel("Telecom limitations", "Call logs, automatic SMS sending, call recording, and call screening are not enabled.")
    }
    private fun safeStartForResult(intent: Intent, code: Int) {
        try { startActivityForResult(intent, code) }
        catch (_: Exception) { toast("No compatible contacts app available") }
    }
    private fun apps() {
        content.addView(label("App launcher", 23f, true))
        listOf(
            "WhatsApp" to "com.whatsapp",
            "Gmail" to "com.google.android.gm",
            "YouTube" to "com.google.android.youtube",
            "Chrome" to "com.android.chrome",
            "Spotify" to "com.spotify.music"
        ).forEach { (name, pkg) -> button("Open $name") { openApp(name, pkg) } }
    }
    private fun settings() {
        content.addView(label("Device & permissions", 23f, true))
        panel("Connection", "Local-only · No remote server paired")
        panel("Security", "No SMS, contacts, microphone, accessibility, or notification permissions requested by Vivian. Speech uses the installed Android speech-recognition activity.")
        button("Android notification access settings") {
            safeStart(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }
        button("Android accessibility settings") {
            safeStart(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        panel("Important", "Opening these settings does not grant Vivian access. Do not enable unrelated services.")
    }
    @Deprecated("Legacy activity result used to keep the starter dependency-free")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == speechRequest && resultCode == RESULT_OK) {
            val spoken = data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if (!spoken.isNullOrBlank()) {
                input?.setText(spoken)
                execute(spoken)
            }
        } else if (requestCode == contactRequest && resultCode == RESULT_OK) {
            toast("Contact selected. Direct contact dialing will be added in a later release.")
        }
    }
}
