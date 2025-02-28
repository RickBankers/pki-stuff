# pki-stuff
PKI stuff
 and docker jenkins ansible

 This configuration includes:

    Resource Group: A container for all resources
    Virtual Network: With separate subnets for VMs and private endpoints
    Log Analytics Workspace: For collecting logs from VMs
    AVD Workspace: The virtual desktop workspace
    AVD Host Pool: A pooled host pool for session hosts
    VM Scale Set: Windows 10 VMs configured for AVD with Azure Monitor Agent
    Private Endpoints: For secure connectivity to:
        AVD Workspace (feed)
        AVD Host Pool (connection)
        Log Analytics Workspace (azuremonitor)
    Private DNS Zones: For name resolution of private endpoints

Key features:

    All resources use private endpoints for secure connectivity
    VM Scale Set includes Azure Monitor Agent extension to send logs to Log Analytics
    Network configuration with separate subnets for VMs and private endpoints
    Basic security configuration with private link support

To use this configuration:

    Save it as main.tf
    Run terraform init
    Run terraform plan to review the changes
    Run terraform apply to create the resources

Additional considerations:

    You might want to add more security configurations (NSGs, etc.)
    Consider using a key vault for secrets management
    Adjust VM sizes, instance counts, and other parameters as needed
    Add diagnostic settings for more detailed monitoring
    Configure AVD-specific settings based on your requirements

This is a basic but functional setup that meets your requirements. Let me know if you need any specific modifications or have questions about the configuration!


# Provider configuration
provider "azurerm" {
  features {}
}

# Variables
variable "location" {
  default = "westeurope"
}

variable "resource_group_name" {
  default = "avd-rg"
}

# Resource Group
resource "azurerm_resource_group" "avd" {
  name     = var.resource_group_name
  location = var.location
}

# Virtual Network and Subnets
resource "azurerm_virtual_network" "avd_vnet" {
  name                = "avd-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
}

resource "azurerm_subnet" "avd_subnet" {
  name                 = "avd-subnet"
  resource_group_name  = azurerm_resource_group.avd.name
  virtual_network_name = azurerm_virtual_network.avd_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "private_endpoint_subnet" {
  name                 = "pe-subnet"
  resource_group_name  = azurerm_resource_group.avd.name
  virtual_network_name = azurerm_virtual_network.avd_vnet.name
  address_prefixes     = ["10.0.2.0/24"]

  private_endpoint_network_policies_enabled     = true
  private_link_service_network_policies_enabled = true
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "avd_logs" {
  name                = "avd-log-analytics"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Virtual Desktop Workspace
resource "azurerm_virtual_desktop_workspace" "avd_workspace" {
  name                = "avd-workspace"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  friendly_name       = "AVD Workspace"
  description         = "Azure Virtual Desktop Workspace"
}

# Virtual Desktop Host Pool
resource "azurerm_virtual_desktop_host_pool" "avd_pool" {
  name                     = "avd-hostpool"
  location                 = azurerm_resource_group.avd.location
  resource_group_name      = azurerm_resource_group.avd.name
  type                     = "Pooled"
  load_balancer_type       = "BreadthFirst"
  maximum_sessions_allowed = 10
  friendly_name            = "AVD Host Pool"
  description              = "Pooled host pool for AVD"
}

# Windows Virtual Machine Scale Set
resource "azurerm_windows_virtual_machine_scale_set" "avd_vmss" {
  name                = "avd-vmss"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  sku                 = "Standard_D2s_v5"
  instances           = 2
  admin_username      = "adminuser"
  admin_password      = "P@ssw0rd1234!"  # Consider using a secret management solution

  source_image_reference {
    publisher = "MicrosoftWindowsDesktop"
    offer     = "Windows-10"
    sku       = "20h2-evd"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "StandardSSD_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "avd-nic"
    primary = true

    ip_configuration {
      name                          = "internal"
      subnet_id                     = azurerm_subnet.avd_subnet.id
      private_ip_address_allocation = "Dynamic"
    }
  }

  # Enable Azure Monitor Agent
  extension {
    name                 = "AzureMonitorWindowsAgent"
    publisher            = "Microsoft.Azure.Monitor"
    type                 = "AzureMonitorWindowsAgent"
    type_handler_version = "1.0"
    settings = jsonencode({
      "workspaceId" = azurerm_log_analytics_workspace.avd_logs.workspace_id
    })
    protected_settings = jsonencode({
      "workspaceKey" = azurerm_log_analytics_workspace.avd_logs.primary_shared_key
    })
  }
}

# Private DNS Zones
resource "azurerm_private_dns_zone" "avd_dns" {
  name                = "privatelink.wvd.microsoft.com"
  resource_group_name = azurerm_resource_group.avd.name
}

resource "azurerm_private_dns_zone" "monitor_dns" {
  name                = "privatelink.monitor.azure.com"
  resource_group_name = azurerm_resource_group.avd.name
}

# Private DNS Zone Virtual Network Links
resource "azurerm_private_dns_zone_virtual_network_link" "avd_dns_link" {
  name                  = "avd-dns-link"
  resource_group_name   = azurerm_resource_group.avd.name
  private_dns_zone_name = azurerm_private_dns_zone.avd_dns.name
  virtual_network_id    = azurerm_virtual_network.avd_vnet.id
}

resource "azurerm_private_dns_zone_virtual_network_link" "monitor_dns_link" {
  name                  = "monitor-dns-link"
  resource_group_name   = azurerm_resource_group.avd.name
  private_dns_zone_name = azurerm_private_dns_zone.monitor_dns.name
  virtual_network_id    = azurerm_virtual_network.avd.id
}

# Private Endpoints
resource "azurerm_private_endpoint" "workspace_pe" {
  name                = "workspace-pe"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  subnet_id           = azurerm_subnet.private_endpoint_subnet.id

  private_service_connection {
    name                           = "workspace-privateserviceconnection"
    private_connection_resource_id = azurerm_virtual_desktop_workspace.avd_workspace.id
    subresource_names              = ["feed"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "avd-dns-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.avd_dns.id]
  }
}

resource "azurerm_private_endpoint" "hostpool_pe" {
  name                = "hostpool-pe"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  subnet_id           = azurerm_subnet.private_endpoint_subnet.id

  private_service_connection {
    name                           = "hostpool-privateserviceconnection"
    private_connection_resource_id = azurerm_virtual_desktop_host_pool.avd_pool.id
    subresource_names              = ["connection"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "avd-dns-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.avd_dns.id]
  }
}

resource "azurerm_private_endpoint" "log_analytics_pe" {
  name                = "loganalytics-pe"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  subnet_id           = azurerm_subnet.private_endpoint_subnet.id

  private_service_connection {
    name                           = "loganalytics-privateserviceconnection"
    private_connection_resource_id = azurerm_log_analytics_workspace.avd_logs.id
    subresource_names              = ["azuremonitor"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "monitor-dns-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.monitor_dns.id]
  }
}



#########################
# Existing resources remain the same until the VMSS section...

# Data Collection Rule for Log Analytics
resource "azurerm_monitor_data_collection_rule" "avd_dcr" {
  name                = "avd-dcr"
  resource_group_name = azurerm_resource_group.avd.name
  location            = azurerm_resource_group.avd.location

  destinations {
    log_analytics {
      workspace_resource_id = azurerm_log_analytics_workspace.avd_logs.id
      name                  = "avd-logs"
    }
  }

  data_flow {
    streams      = ["Microsoft-Event", "Microsoft-Perf", "Microsoft-WindowsEvent"]
    destinations = ["avd-logs"]
  }

  data_sources {
    windows_event_log {
      name    = "eventLogs"
      streams = ["Microsoft-Event"]
      x_path_queries = [
        "Application!*[System[(Level=1 or Level=2 or Level=3 or Level=4 or Level=5)]]",
        "System!*[System[(Level=1 or Level=2 or Level=3 or Level=4 or Level=5)]]",
        "Microsoft-Windows-TerminalServices-RemoteConnectionManager/*",
        "Microsoft-Windows-TerminalServices-LocalSessionManager/*",
        "Microsoft-Windows-RemoteDesktopServices-RdpCoreTS/*"
      ]
    }

    performance_counter {
      name                          = "perfCounters"
      streams                      = ["Microsoft-Perf"]
      sampling_frequency_in_seconds = 60
      counter_specifiers = [
        "\\Processor(_Total)\\% Processor Time",
        "\\Memory\\Available MBytes",
        "\\Network Interface(*)\\Bytes Total/sec"
      ]
    }
  }

  description = "Data collection rule for AVD monitoring"
}

# Data Collection Endpoint (required for AMA)
resource "azurerm_monitor_data_collection_endpoint" "avd_dce" {
  name                = "avd-dce"
  resource_group_name = azurerm_resource_group.avd.name
  location            = azurerm_resource_group.avd.location
}

# Updated Windows Virtual Machine Scale Set
resource "azurerm_windows_virtual_machine_scale_set" "avd_vmss" {
  name                = "avd-vmss"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  sku                 = "Standard_D2s_v5"
  instances           = 2
  admin_username      = "adminuser"
  admin_password      = "P@ssw0rd1234!"  # Consider using a secret management solution

  source_image_reference {
    publisher = "MicrosoftWindowsDesktop"
    offer     = "Windows-10"
    sku       = "20h2-evd"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "StandardSSD_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "avd-nic"
    primary = true

    ip_configuration {
      name                          = "internal"
      subnet_id                     = azurerm_subnet.avd_subnet.id
      private_ip_address_allocation = "Dynamic"
    }
  }

  # Azure Monitor Agent Extension
  extension {
    name                 = "AzureMonitorWindowsAgent"
    publisher            = "Microsoft.Azure.Monitor"
    type                 = "AzureMonitorWindowsAgent"
    type_handler_version = "1.0"
    auto_upgrade_minor_version = true

    settings = jsonencode({
      "authentication" = {
        "managedIdentity" = {
          "identifier" = "mi_res_id"
        }
      }
    })
  }

  # AVD Agent Installation (required for Virtual Desktop functionality)
  extension {
    name                 = "AVDAgent"
    publisher            = "Microsoft.Azure.VirtualDesktop"
    type                 = "AgentInstaller"
    type_handler_version = "1.0"
    settings = jsonencode({
      "registrationInfo" = {
        "registrationToken" = azurerm_virtual_desktop_host_pool.avd_pool.registration_info[0].token
      }
    })
  }

  # Dependency Agent for additional monitoring (optional)
  extension {
    name                 = "DependencyAgentWindows"
    publisher            = "Microsoft.Azure.Monitoring.DependencyAgent"
    type                 = "DependencyAgentWindows"
    type_handler_version = "9.10"
    auto_upgrade_minor_version = true
  }

  identity {
    type = "SystemAssigned"
  }

  # Link to Data Collection Rule
  depends_on = [azurerm_monitor_data_collection_rule.avd_dcr]
}

# Data Collection Rule Association
resource "azurerm_monitor_data_collection_rule_association" "avd_vmss_dcr" {
  name                    = "avd-vmss-dcr-association"
  target_resource_id      = azurerm_windows_virtual_machine_scale_set.avd_vmss.id
  data_collection_rule_id = azurerm_monitor_data_collection_rule.avd_dcr.id
  description             = "Associate VMSS with AVD data collection rule"
}

# Rest of the configuration (private endpoints, etc.) remains the same...
Key changes and additions:

    Data Collection Rule (DCR):
        Collects Windows Event Logs including AVD-specific channels:
            TerminalServices-RemoteConnectionManager
            TerminalServices-LocalSessionManager
            RemoteDesktopServices-RdpCoreTS
        Collects performance counters
        Sends data to the Log Analytics Workspace
    Data Collection Endpoint (DCE):
        Required infrastructure for the Azure Monitor Agent
    VMSS Updates:
        Added Azure Monitor Agent extension with managed identity
        Added AVD Agent extension to register with the host pool
        Added optional Dependency Agent for deeper monitoring
        Included system-assigned managed identity
        Associated with the DCR
    DCR Association:
        Links the VMSS to the data collection rule

This configuration will:

    Install the AVD Agent on the VMs
    Collect system logs, application logs, and AVD-specific logs
    Send all collected logs to the Log Analytics Workspace
    Maintain the private endpoint connectivity

To verify the logs:

    After deployment, wait for the agents to initialize (15-30 minutes)
    In the Azure Portal, go to Log Analytics Workspace > Logs
    Run queries like:
    kql

    Event
    | where Source contains "TerminalServices" or Source contains "RemoteDesktop"
    | order by TimeGenerated desc

Note: You might need to adjust the specific event channels or add more based on your monitoring requirements. The included channels cover the core AVD functionality, but additional channels might be needed for specific scenarios.
