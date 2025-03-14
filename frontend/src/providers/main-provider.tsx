'use client'

import { Toaster } from '@/components/ui/common/sonner'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type PropsWithChildren, useState } from 'react'

export function MainProvider({ children }: PropsWithChildren) {
	const [client] = useState(
		new QueryClient({
			defaultOptions: {
				queries: {
					refetchOnWindowFocus: true,
					staleTime: 1000,
				}
			}
		})
	)

	return (
		<QueryClientProvider client={client}>
			{children}
			<Toaster position='top-0'/>
		</QueryClientProvider>
	)
}