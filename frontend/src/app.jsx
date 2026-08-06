import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { ShieldAlert, Send, Trash2, Bot, User } from 'lucide-react'

export default function App() {
    //state
    const [messages, setMessages] = useState([
        {
            sender: 'bot',
            text: 'Halo! Saya **VulnCopilot**, asisten DevSecOps RAG AI Anda. Silakan tanyakan seputar kerentanan keamanan, OWASP Top 10, atau keamanan kode!'
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const chatEndRef = useRef()

    // Auto scroll when new messages
    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, loading])

    // send message to FastAPI backend
    const handleSend = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = input.trim()
        setInput('')
        // add user message to chat view
        setMessages((prev) => [...prev, { sender: 'user', text: userMessage }])
        setLoading(true)

        try {
            // call HTTP POST streaming endpoint to FastAPI backend
            const response = await fetch('http://localhost:8000/chat-stream', {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage })
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                setMessages((prev) => [...prev, { sender: 'bot', text: `Error: ${errorData.detail || 'Gagal memproses pesan.'}` }])
                setLoading(false)
                return
            }

            // Create a placeholder bot message for streaming text
            setMessages((prev) => [...prev, { sender: 'bot', text: '' }])
            setLoading(false)

            const reader = response.body.getReader()
            const decoder = new TextDecoder()

            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                const chunk = decoder.decode(value, { stream: true })
                setMessages((prev) => {
                    const newMessages = [...prev]
                    const lastIndex = newMessages.length - 1
                    if (lastIndex >= 0 && newMessages[lastIndex].sender === 'bot') {
                        newMessages[lastIndex] = {
                            ...newMessages[lastIndex],
                            text: newMessages[lastIndex].text + chunk
                        }
                    }
                    return newMessages
                })
            }
        } catch (error) {
            setMessages((prev) => [...prev, { sender: 'bot', text: 'Error tidak dapat terhubung ke backend' }])
            setLoading(false)
        }
    }

    // Function Reset Chatting Memory
    const handleReset = async () => {
        if (!window.confirm(`Apakah kamu yakin ingin mereset seluruh histori chatting?`))
            return
        try {
            const response = await fetch('http://localhost:8000/reset-session', {
                method: "POST"
            })
            const data = await response.json()
            if (response.ok && data.status === 'success') {
                alert(data.message)
                setMessages([
                    {
                        sender: 'bot',
                        text: 'Memori percakapan telah di-reset, silakan ajukan pertanyaan lagi.'
                    }
                ])
            } else {
                alert(`Gagal mereset percakapan: ${data.message || 'Terjadi kesalahan.'}`)
            }
        } catch (error) {
            alert("Error tidak dapat terhubung ke server saat mereset memori")
        }
    }

    return (
        <div className="app-container">
            { }
            <header className="app-header">
                <div className="brand">
                    <ShieldAlert className="brand-icon" size={28} />
                    <div className="brand-title">
                        <h1>VulnCopilot RAG</h1>
                        <p>DevSecOps Security Intelligence AI</p>
                    </div>
                </div>
                <button className="reset-btn" onClick={handleReset} title="Reset Percakapan">
                    <Trash2 size={16} /> Reset Chat
                </button>
            </header>

            {/* Body / Area Pesan Chat */}
            <main className="chat-body">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender}`}>
                        <div className="avatar">
                            {msg.sender === 'user' ? <User size={20} /> : <Bot size={20} />}
                        </div>
                        <div className="bubble">
                            {msg.sender === 'bot' ? (
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                            ) : (
                                msg.text
                            )}
                        </div>
                    </div>
                ))}

                {/* Indicator saat AI sedang berpikir */}
                {loading && (
                    <div className="message bot">
                        <div className="avatar">
                            <Bot size={20} />
                        </div>
                        <div className="bubble">
                            <div className="typing-indicator">
                                <div className="dot"></div>
                                <div className="dot"></div>
                                <div className="dot"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </main>

            {/* Footer / Form Input */}
            <footer className="chat-footer">
                <form onSubmit={handleSend} className="input-form">
                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Tanyakan kerentanan kode atau keamanan..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
                        <Send size={18} />Kirim
                    </button>
                </form>
            </footer>
        </div>

    )
}