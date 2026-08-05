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
    const scrollRef = useRef()

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
        if (!input.trim() || looading) return

        const userMessage = input.trim()
        setInput('')
        // add user message to chat view
        setMessages((prev) => [...prev, { sender: 'user', text: userMessage }])
        setLoading(true)

        try {
            // call HTTP POST to FastAPI backend
            const response = await fetch('http://localhost:8000/chat', {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage })
            })
        }
    }
}