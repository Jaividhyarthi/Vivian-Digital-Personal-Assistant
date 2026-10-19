package ai.vivian.companion

import android.app.Activity
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {
    private val green = android.graphics.Color.rgb(45, 93, 71)
    private val cream = android.graphics.Color.rgb(248, 248, 242)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 48, 32, 32)
            setBackgroundColor(cream)
        }
        val scroll = ScrollView(this)
        scroll.addView(root)
        setContentView(scroll)

        fun heading(text: String, size: Float = 19f) {
            root.addView(TextView(this).apply {
                this.text = text
                textSize = size
                setTextColor(green)
                setPadding(0, 18, 0, 12)
                gravity = Gravity.START
            })
        }
        fun button(label: String, action: () -> Unit) {
            root.addView(Button(this).apply {
                text = label
                setOnClickListener { action() }
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
            })
        }
        heading("VIVIAN", 30f)
        heading("Android Companion · v0.1")
        heading("Device: ${Build.MANUFACTURER} ${Build.MODEL}")
        heading("Android: ${Build.VERSION.RELEASE}")
        heading("Status: Local-only · Not paired")
        heading("Open an installed app")
        val apps = listOf(
            "WhatsApp" to "com.whatsapp",
            "Gmail" to "com.google.android.gm",
            "YouTube" to "com.google.android.youtube",
            "Chrome" to "com.android.chrome",
            "Spotify" to "com.spotify.music"
        )
        apps.forEach { (name, packageName) ->
            button("Open $name") {
                val launch = packageManager.getLaunchIntentForPackage(packageName)
                if (launch != null) startActivity(launch)
                else android.widget.Toast.makeText(
                    this, "$name is not installed or not visible", android.widget.Toast.LENGTH_SHORT
                ).show()
            }
        }
        heading("Device settings")
        button("Open notification access settings") {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }
        button("Open accessibility settings") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        heading("Safety: Vivian cannot read notifications, inspect screens, or control other apps yet. Opening settings does not grant Vivian those permissions.")
    }
}
