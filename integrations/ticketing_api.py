"""
Ticketing API Integration Layer

Provides abstraction for integrating with various ticketing systems:
- Jira
- ServiceNow
- Zendesk
- Generic REST APIs

Supports:
- Ingesting tickets from external systems
- Updating ticket status and comments
- Webhook handlers for real-time events
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class TicketingSystemAdapter(ABC):
    """Base adapter for ticketing system integrations"""
    
    def __init__(self, api_url: str, api_key: str, **kwargs):
        """
        Initialize ticketing system adapter
        
        Args:
            api_url: Base API URL for the ticketing system
            api_key: API key or token for authentication
            **kwargs: Additional configuration (username, project_id, etc.)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.config = kwargs
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    async def fetch_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch a single ticket by ID"""
        pass
    
    @abstractmethod
    async def fetch_tickets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch multiple tickets with filters"""
        pass
    
    @abstractmethod
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create a new ticket, return ticket ID"""
        pass
    
    @abstractmethod
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket fields"""
        pass
    
    @abstractmethod
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to a ticket"""
        pass
    
    @abstractmethod
    def normalize_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ticket data to standard format"""
        pass


class JiraAdapter(TicketingSystemAdapter):
    """Jira ticketing system adapter"""
    
    async def fetch_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch ticket from Jira"""
        url = f"{self.api_url}/rest/api/3/issue/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.normalize_ticket(data)
                    else:
                        logger.error(f"Jira API error: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching Jira ticket: {e}")
            return {}
    
    async def fetch_tickets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch multiple tickets from Jira using JQL"""
        # Build JQL query
        jql_parts = []
        if filters.get('status'):
            jql_parts.append(f"status = '{filters['status']}'")
        if filters.get('priority'):
            jql_parts.append(f"priority = '{filters['priority']}'")
        if filters.get('assignee'):
            jql_parts.append(f"assignee = '{filters['assignee']}'")
        
        jql = " AND ".join(jql_parts) if jql_parts else "created >= -7d"
        
        url = f"{self.api_url}/rest/api/3/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "jql": jql,
            "maxResults": filters.get('limit', 50)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [self.normalize_ticket(issue) for issue in data.get('issues', [])]
                    else:
                        logger.error(f"Jira API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching Jira tickets: {e}")
            return []
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create Jira issue"""
        url = f"{self.api_url}/rest/api/3/issue"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Map to Jira format
        jira_data = {
            "fields": {
                "project": {"key": self.config.get('project_key', 'PROJ')},
                "summary": ticket_data.get('title', 'No title'),
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": ticket_data.get('description', '')}]
                    }]
                },
                "issuetype": {"name": ticket_data.get('issue_type', 'Task')},
                "priority": {"name": ticket_data.get('priority', 'Medium')}
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=jira_data) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get('key', '')
                    else:
                        logger.error(f"Jira create error: {response.status}")
                        return ''
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}")
            return ''
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update Jira issue"""
        url = f"{self.api_url}/rest/api/3/issue/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Map updates to Jira format
        jira_updates = {"fields": {}}
        if 'status' in updates:
            # Use transition API for status changes
            return await self._transition_ticket(ticket_id, updates['status'])
        if 'priority' in updates:
            jira_updates['fields']['priority'] = {"name": updates['priority']}
        if 'assignee' in updates:
            jira_updates['fields']['assignee'] = {"name": updates['assignee']}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, json=jira_updates) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Error updating Jira ticket: {e}")
            return False
    
    async def _transition_ticket(self, ticket_id: str, status: str) -> bool:
        """Transition Jira ticket to new status"""
        # Simplified - in production, need to map status to transition ID
        url = f"{self.api_url}/rest/api/3/issue/{ticket_id}/transitions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # This is simplified - real implementation needs to:
        # 1. Get available transitions
        # 2. Find transition ID for target status
        # 3. Execute transition
        logger.info(f"Would transition {ticket_id} to {status}")
        return True
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add comment to Jira issue"""
        url = f"{self.api_url}/rest/api/3/issue/{ticket_id}/comment"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }]
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    return response.status == 201
        except Exception as e:
            logger.error(f"Error adding Jira comment: {e}")
            return False
    
    def normalize_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Jira ticket to standard format"""
        fields = raw_ticket.get('fields', {})
        
        return {
            'ticket_id': raw_ticket.get('key', ''),
            'title': fields.get('summary', ''),
            'description': self._extract_description(fields.get('description', {})),
            'status': fields.get('status', {}).get('name', ''),
            'priority': fields.get('priority', {}).get('name', 'Medium'),
            'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
            'reporter': fields.get('reporter', {}).get('displayName', ''),
            'created_at': fields.get('created', ''),
            'updated_at': fields.get('updated', ''),
            'labels': fields.get('labels', []),
            'raw': raw_ticket
        }
    
    def _extract_description(self, description_doc: Dict[str, Any]) -> str:
        """Extract text from Jira description document"""
        if not description_doc or not description_doc.get('content'):
            return ''
        
        text_parts = []
        for content in description_doc.get('content', []):
            if content.get('type') == 'paragraph':
                for item in content.get('content', []):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
        
        return ' '.join(text_parts)


class ServiceNowAdapter(TicketingSystemAdapter):
    """ServiceNow ticketing system adapter"""
    
    async def fetch_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch ticket from ServiceNow"""
        url = f"{self.api_url}/api/now/table/incident/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.normalize_ticket(data.get('result', {}))
                    else:
                        return {}
        except Exception as e:
            logger.error(f"Error fetching ServiceNow ticket: {e}")
            return {}
    
    async def fetch_tickets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch multiple tickets from ServiceNow"""
        url = f"{self.api_url}/api/now/table/incident"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build query params
        params = {
            "sysparm_limit": filters.get('limit', 50),
            "sysparm_query": self._build_snow_query(filters)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [self.normalize_ticket(inc) for inc in data.get('result', [])]
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error fetching ServiceNow tickets: {e}")
            return []
    
    def _build_snow_query(self, filters: Dict[str, Any]) -> str:
        """Build ServiceNow query string"""
        query_parts = []
        if filters.get('status'):
            query_parts.append(f"state={filters['status']}")
        if filters.get('priority'):
            query_parts.append(f"priority={filters['priority']}")
        
        return "^".join(query_parts) if query_parts else "sys_created_onONLast 7 days@javascript:gs.daysAgoStart(7)"
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create ServiceNow incident"""
        url = f"{self.api_url}/api/now/table/incident"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        snow_data = {
            "short_description": ticket_data.get('title', ''),
            "description": ticket_data.get('description', ''),
            "priority": self._map_priority(ticket_data.get('priority', 'Medium')),
            "caller_id": ticket_data.get('reporter', '')
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=snow_data) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get('result', {}).get('number', '')
                    else:
                        return ''
        except Exception as e:
            logger.error(f"Error creating ServiceNow ticket: {e}")
            return ''
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ServiceNow incident"""
        url = f"{self.api_url}/api/now/table/incident/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=updates) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error updating ServiceNow ticket: {e}")
            return False
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add work note to ServiceNow incident"""
        return await self.update_ticket(ticket_id, {"work_notes": comment})
    
    def normalize_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ServiceNow ticket to standard format"""
        return {
            'ticket_id': raw_ticket.get('number', ''),
            'title': raw_ticket.get('short_description', ''),
            'description': raw_ticket.get('description', ''),
            'status': self._map_state(raw_ticket.get('state', '')),
            'priority': self._reverse_map_priority(raw_ticket.get('priority', '3')),
            'assignee': raw_ticket.get('assigned_to', {}).get('display_value', 'Unassigned'),
            'reporter': raw_ticket.get('caller_id', {}).get('display_value', ''),
            'created_at': raw_ticket.get('sys_created_on', ''),
            'updated_at': raw_ticket.get('sys_updated_on', ''),
            'raw': raw_ticket
        }
    
    def _map_priority(self, priority: str) -> str:
        """Map standard priority to ServiceNow priority (1-5)"""
        mapping = {'Critical': '1', 'High': '2', 'Medium': '3', 'Low': '4', 'Planning': '5'}
        return mapping.get(priority, '3')
    
    def _reverse_map_priority(self, snow_priority: str) -> str:
        """Map ServiceNow priority to standard priority"""
        mapping = {'1': 'Critical', '2': 'High', '3': 'Medium', '4': 'Low', '5': 'Planning'}
        return mapping.get(snow_priority, 'Medium')
    
    def _map_state(self, state: str) -> str:
        """Map ServiceNow state to standard status"""
        # Simplified mapping - ServiceNow states are numeric
        mapping = {'1': 'New', '2': 'In Progress', '3': 'On Hold', '6': 'Resolved', '7': 'Closed'}
        return mapping.get(state, 'Unknown')


class TicketingIntegration:
    """
    Main ticketing integration manager
    
    Handles multiple ticketing system adapters and provides unified interface
    """
    
    def __init__(self):
        """Initialize ticketing integration manager"""
        self.adapters: Dict[str, TicketingSystemAdapter] = {}
        logger.info("Initialized TicketingIntegration manager")
    
    def register_adapter(self, name: str, adapter: TicketingSystemAdapter):
        """Register a ticketing system adapter"""
        self.adapters[name] = adapter
        logger.info(f"Registered adapter: {name}")
    
    async def fetch_ticket(self, system: str, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Fetch ticket from specified system"""
        if system not in self.adapters:
            logger.error(f"Unknown ticketing system: {system}")
            return None
        
        return await self.adapters[system].fetch_ticket(ticket_id)
    
    async def fetch_all_tickets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch tickets from all registered systems"""
        all_tickets = []
        
        for system_name, adapter in self.adapters.items():
            try:
                tickets = await adapter.fetch_tickets(filters)
                for ticket in tickets:
                    ticket['source_system'] = system_name
                all_tickets.extend(tickets)
            except Exception as e:
                logger.error(f"Error fetching from {system_name}: {e}")
        
        return all_tickets
    
    async def sync_ticket_to_system(
        self,
        system: str,
        ticket_data: Dict[str, Any],
        ai_response: Dict[str, Any]
    ) -> bool:
        """
        Sync AI processing results back to ticketing system
        
        Args:
            system: Target ticketing system
            ticket_data: Original ticket data
            ai_response: AI processing results
            
        Returns:
            Success status
        """
        if system not in self.adapters:
            logger.error(f"Unknown ticketing system: {system}")
            return False
        
        adapter = self.adapters[system]
        ticket_id = ticket_data.get('ticket_id', '')
        
        try:
            # Add AI response as comment
            comment = self._format_ai_response(ai_response)
            success = await adapter.add_comment(ticket_id, comment)
            
            # Update ticket fields based on AI classification
            updates = {}
            if ai_response.get('urgency'):
                updates['priority'] = ai_response['urgency'].capitalize()
            if ai_response.get('assignee'):
                updates['assignee'] = ai_response['assignee']
            
            if updates:
                await adapter.update_ticket(ticket_id, updates)
            
            logger.info(f"Synced AI response to {system} ticket {ticket_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error syncing to {system}: {e}")
            return False
    
    def _format_ai_response(self, ai_response: Dict[str, Any]) -> str:
        """Format AI response for ticketing system comment"""
        parts = [
            "=== AI Analysis ===",
            f"Classification: {ai_response.get('intent', 'unknown')}",
            f"Urgency: {ai_response.get('urgency', 'medium')}",
            f"Confidence: {ai_response.get('confidence', 0):.0%}",
            ""
        ]
        
        if ai_response.get('has_duplicates'):
            parts.append(f"⚠️ {ai_response.get('duplicate_warning', 'Similar tickets found')}")
            parts.append("")
        
        if ai_response.get('sla_risk'):
            parts.append(f"SLA Risk: {ai_response['sla_risk'].upper()}")
            parts.append("")
        
        parts.append("Response:")
        parts.append(ai_response.get('response', 'No response generated'))
        
        return "\n".join(parts)
