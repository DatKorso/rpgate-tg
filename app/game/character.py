"""Character sheet model for RPG mechanics."""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4


class CharacterSheet(BaseModel):
    """Character sheet model for player."""
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    telegram_user_id: int
    name: str
    
    # Core Stats (D&D style)
    level: int = Field(default=1, ge=1, le=20)
    
    # Attributes (modifiers from -5 to +10)
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)
    
    # Combat Stats
    hp: int = Field(default=20, ge=0)
    max_hp: int = Field(default=20, ge=1)
    armor_class: int = Field(default=10, ge=0)
    
    # Inventory
    gold: int = Field(default=50, ge=0)
    inventory: list[str] = Field(default_factory=lambda: ["меч", "кожаная броня", "зелье лечения"])
    
    # Location
    location: str = Field(default="tavern")
    
    # Experience
    xp: int = Field(default=0, ge=0)
    
    @property
    def strength_mod(self) -> int:
        """Calculate strength modifier from attribute."""
        return (self.strength - 10) // 2
    
    @property
    def dexterity_mod(self) -> int:
        """Calculate dexterity modifier from attribute."""
        return (self.dexterity - 10) // 2
    
    @property
    def constitution_mod(self) -> int:
        """Calculate constitution modifier from attribute."""
        return (self.constitution - 10) // 2
    
    @property
    def intelligence_mod(self) -> int:
        """Calculate intelligence modifier from attribute."""
        return (self.intelligence - 10) // 2
    
    @property
    def wisdom_mod(self) -> int:
        """Calculate wisdom modifier from attribute."""
        return (self.wisdom - 10) // 2
    
    @property
    def charisma_mod(self) -> int:
        """Calculate charisma modifier from attribute."""
        return (self.charisma - 10) // 2
    
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.hp > 0
    
    def take_damage(self, damage: int) -> int:
        """
        Apply damage to character.
        
        Args:
            damage: Amount of damage to take
            
        Returns:
            Actual damage taken (clamped to current HP)
        """
        damage = max(0, damage)
        old_hp = self.hp
        self.hp = max(0, self.hp - damage)
        actual_damage = old_hp - self.hp
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal character.
        
        Args:
            amount: Amount of HP to restore
            
        Returns:
            Actual HP restored (clamped to max HP)
        """
        amount = max(0, amount)
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        actual_healing = self.hp - old_hp
        return actual_healing
    
    def model_dump_for_storage(self) -> dict:
        """Export for storage in FSM context or DB."""
        return self.model_dump(mode='json')
